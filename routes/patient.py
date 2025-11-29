from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Prescription, Department, DoctorAvailability
from services import QueueService
from datetime import datetime, timedelta, time as dt_time
from extensions import socketio
from functools import wraps
import qrcode
import io
import base64
import os

patient_bp = Blueprint('patient', __name__)
queue_service = QueueService()

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_patient():
            flash('Access denied. Patient account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    queue_position = queue_service.get_position(current_user.id)
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status == 'scheduled',
        Appointment.appointment_date >= datetime.utcnow()
    ).order_by(Appointment.appointment_date).all()
    
    medical_records = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    estimated_wait = None
    doctor_name = None
    if queue_position:
        doctor = User.query.get(queue_position['doctor_id'])
        if doctor:
            estimated_wait = (queue_position['position'] - 1) * doctor.avg_consultation_time
            doctor_name = doctor.full_name
        
        # Get the QueueEntry ID for the API
        queue_entry = QueueEntry.query.filter_by(
            patient_id=current_user.id,
            doctor_id=queue_position['doctor_id'],
            status='waiting'
        ).first()
        if queue_entry:
            queue_position['id'] = queue_entry.id
    
    return render_template(
        'patient/dashboard.html',
        queue_position=queue_position,
        estimated_wait=estimated_wait,
        appointments=upcoming_appointments,
        medical_records=medical_records,
        doctor_name=doctor_name
    )

@patient_bp.route('/book-appointment', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        slot_time = request.form.get('slot_time')
        symptoms = request.form.get('symptoms')
        
        # Convert doctor_id to int
        try:
            doctor_id = int(doctor_id)
        except (ValueError, TypeError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Invalid doctor selected.'})
            flash('Invalid doctor selected.', 'danger')
            return redirect(url_for('patient.book_appointment'))
        
        doctor = User.query.get(doctor_id)
        if not doctor or not doctor.is_doctor():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Invalid doctor selected.'})
            flash('Invalid doctor selected.', 'danger')
            return redirect(url_for('patient.book_appointment'))
        # parse appointment datetime
        try:
            appointment_dt = datetime.strptime(f"{appointment_date} {slot_time}", '%Y-%m-%d %H:%M')
        except Exception:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Invalid date/time format.'})
            flash('Invalid date/time format.', 'danger')
            return redirect(url_for('patient.book_appointment'))

        if appointment_dt < datetime.utcnow():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Cannot book an appointment in the past.'})
            flash('Cannot book an appointment in the past.', 'danger')
            return redirect(url_for('patient.book_appointment'))

        # check doctor availability for that day/time
        day_of_week = appointment_dt.weekday()  # Monday=0
        slot = appointment_dt.time()

        avail_entries = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_available=True
        ).all()

        is_slot_ok = False
        for av in avail_entries:
            if av.start_time <= slot <= av.end_time:
                is_slot_ok = True
                break

        if not is_slot_ok and len(avail_entries) > 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Selected slot is outside the doctor\'s availability. Please choose another time.'})
            flash('Selected slot is outside the doctor\'s availability. Please choose another time.', 'danger')
            return redirect(url_for('patient.book_appointment'))

        # Ensure department_id is set, use a default if doctor has no department
        department_id = doctor.department_id
        if not department_id:
            # Try to get a default department or create appointment without department
            default_dept = Department.query.filter_by(is_active=True).first()
            if default_dept:
                department_id = default_dept.id
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': 'Doctor has no department assigned. Please contact administration.'})
                flash('Doctor has no department assigned. Please contact administration.', 'danger')
                return redirect(url_for('patient.book_appointment'))
        
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            department_id=department_id,
            appointment_type='scheduled',
            appointment_date=appointment_dt,
            slot_time=slot_time,
            symptoms=symptoms,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        # notify the doctor in real-time (if connected)
        try:
            socketio.emit('appointment:created', {
                'appointment_id': appointment.id,
                'doctor_id': int(doctor_id),
                'patient_id': current_user.id,
                'appointment_date': appointment.appointment_date.isoformat()
            }, room=f'doctor_{doctor_id}')
        except Exception:
            # non-fatal: continue even if notification fails
            pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect_url': url_for('patient.dashboard'), 'message': 'Appointment booked successfully!'})
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.dashboard'))
    
    departments = Department.query.filter_by(is_active=True).all()
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    return render_template(
        'patient/book_appointment.html',
        departments=departments,
        doctors=doctors,
        now=datetime.utcnow()
    )

@patient_bp.route('/join-queue/<int:doctor_id>')
@login_required
@patient_required
def join_queue(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    if not doctor.is_doctor():
        flash('Invalid doctor.', 'danger')
        return redirect(url_for('patient.dashboard'))
    
    existing_position = queue_service.get_position(current_user.id)
    if existing_position:
        flash('You are already in a queue. Please complete that consultation first.', 'warning')
        return redirect(url_for('patient.dashboard'))
    
    queue_entry = QueueEntry(
        patient_id=current_user.id,
        doctor_id=doctor_id,
        status='waiting',
        priority=0
    )
    db.session.add(queue_entry)
    db.session.commit()
    
    queue_service.enqueue(current_user.id, doctor_id, priority=0)
    # notify doctor and patient about queue update
    try:
        current_queue = queue_service.get_queue(doctor_id)
        socketio.emit('queue:update', {'doctor_id': doctor_id, 'queue': current_queue}, room=f'doctor_{doctor_id}')
        # notify the patient specifically
        position_info = queue_service.get_position(current_user.id)
        socketio.emit('queue:joined', {'position': position_info}, room=f'user_{current_user.id}')
    except Exception:
        pass

    flash(f'You have joined Dr. {doctor.full_name}\'s queue.', 'success')
    return redirect(url_for('patient.dashboard'))

@patient_bp.route('/leave-queue')
@login_required
@patient_required
def leave_queue():
    queue_service.remove_from_queue(current_user.id)
    
    queue_entry = QueueEntry.query.filter_by(
        patient_id=current_user.id,
        status='waiting'
    ).first()
    
    if queue_entry:
        queue_entry.status = 'cancelled'
        db.session.commit()
    # emit update to doctor and patient
    try:
        # if we stored doctor_id in queue_entry earlier, use it; else attempt to fetch position
        if queue_entry:
            socketio.emit('queue:update', {'doctor_id': queue_entry.doctor_id, 'queue': queue_service.get_queue(queue_entry.doctor_id)}, room=f'doctor_{queue_entry.doctor_id}')
        socketio.emit('queue:left', {'patient_id': current_user.id}, room=f'user_{current_user.id}')
    except Exception:
        pass

    flash('You have left the queue.', 'info')
    return redirect(url_for('patient.dashboard'))

@patient_bp.route('/medical-history')
@login_required
@patient_required
def medical_history():
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = MedicalRecord.query.filter_by(patient_id=current_user.id)
    
    if search:
        query = query.filter(
            db.or_(
                MedicalRecord.symptoms.ilike(f'%{search}%'),
                MedicalRecord.diagnosis.ilike(f'%{search}%'),
                MedicalRecord.notes.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        ).join(User, MedicalRecord.doctor_id == User.id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(MedicalRecord.visit_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(MedicalRecord.visit_date <= date_to_obj)
        except ValueError:
            pass
    
    records = query.order_by(MedicalRecord.visit_date.desc()).all()
    
    return render_template('patient/medical_history.html', records=records, search=search, date_from=date_from, date_to=date_to)

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Prescription.query.filter_by(patient_id=current_user.id)
    
    if search:
        query = query.join(User, Prescription.doctor_id == User.id).filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                Prescription.instructions.ilike(f'%{search}%')
            )
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Prescription.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Prescription.created_at <= date_to_obj)
        except ValueError:
            pass
    
    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient/prescriptions.html', prescriptions=prescriptions, search=search, date_from=date_from, date_to=date_to)


@patient_bp.route('/prescriptions/<int:prescription_id>/download')
@login_required
@patient_required
def download_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)

    if prescription.patient_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patient.prescriptions'))

    buffer = io.BytesIO()
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "MediQueue - Medical Prescription")

    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Date: {prescription.created_at.strftime('%Y-%m-%d')}")
    p.drawString(100, 700, f"Doctor: Dr. {prescription.doctor.full_name}")
    p.drawString(100, 680, f"Patient: {prescription.patient.full_name}")

    p.drawString(100, 650, "Medications:")
    y = 630
    if prescription.medications:
        for med in prescription.medications:
            if isinstance(med, dict):
                p.drawString(120, y, f"- {med.get('medication', 'N/A')} ({med.get('dosage', 'N/A')}) - {med.get('frequency', 'N/A')}")
            else:
                p.drawString(120, y, f"- {str(med)}")
            y -= 20

    p.drawString(100, y - 20, "Instructions:")
    p.drawString(120, y - 40, str(prescription.instructions) if prescription.instructions else "None")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'prescription_{prescription_id}.pdf', mimetype='application/pdf')

@patient_bp.route('/qr-checkin')
@login_required
@patient_required
def qr_checkin():
    qr_data = f"patient:{current_user.id}:{current_user.email}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('patient/qr_checkin.html', qr_code=img_base64)

@patient_bp.route('/download-report/<int:record_id>')
@login_required
@patient_required
def download_report(record_id):
    record = MedicalRecord.query.get_or_404(record_id)
    if record.patient_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('patient.medical_history'))
    
    if not record.report_file:
        flash('No report file available for this record.', 'warning')
        return redirect(url_for('patient.medical_history'))
    
    return send_file(
        os.path.join(current_app.config['UPLOAD_FOLDER'], record.report_file),
        as_attachment=True
    )
