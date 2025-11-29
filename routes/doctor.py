from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Prescription, Department, DoctorAvailability
from services import QueueService
from datetime import datetime, timedelta, time as dt_time
from functools import wraps
import io
import json
import os
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from extensions import socketio

doctor_bp = Blueprint('doctor', __name__)
queue_service = QueueService()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_doctor():
            flash('Access denied. Doctor privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    queue_list = queue_service.get_queue(current_user.id)
    
    today = datetime.utcnow().date()
    appointments_today = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        db.func.date(Appointment.appointment_date) == today
    ).all()
    
    patients_served_today = QueueEntry.query.filter(
        QueueEntry.doctor_id == current_user.id,
        QueueEntry.status == 'completed',
        db.func.date(QueueEntry.completed_at) == today
    ).count()
    
    active_queue_entries = []
    for queue_item in queue_list:
        patient = User.query.get(queue_item['patient_id'])
        if patient:
            queue_item['patient'] = patient
            active_queue_entries.append(queue_item)
    
    return render_template(
        'doctor/dashboard.html',
        queue=active_queue_entries,
        appointments=appointments_today,
        patients_served=patients_served_today,
        queue_length=len(queue_list)
    )

@doctor_bp.route('/select-patient', methods=['GET', 'POST'])
@login_required
@doctor_required
def select_patient():
    """Allow doctors to search and select any patient"""
    search = request.args.get('search', '')
    patients = []
    
    if search:
        patients = User.query.filter(
            User.role == 'patient',
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%')
            )
        ).limit(50).all()
    else:
        # Show recent patients (patients with appointments or records with this doctor)
        appointment_patient_ids = db.session.query(Appointment.patient_id).filter(
            Appointment.doctor_id == current_user.id
        ).distinct().all()
        
        record_patient_ids = db.session.query(MedicalRecord.patient_id).filter(
            MedicalRecord.doctor_id == current_user.id
        ).distinct().all()
        
        # Combine and get unique patient IDs
        patient_ids = set()
        for pid_tuple in appointment_patient_ids:
            patient_ids.add(pid_tuple[0])
        for pid_tuple in record_patient_ids:
            patient_ids.add(pid_tuple[0])
        
        if patient_ids:
            patients = User.query.filter(
                User.id.in_(list(patient_ids)),
                User.role == 'patient'
            ).limit(20).all()
    
    return render_template('doctor/select_patient.html', patients=patients, search=search)

@doctor_bp.route('/patient/<int:patient_id>')
@login_required
@doctor_required
def view_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_date.desc()).all()
    
    return render_template(
        'doctor/patient_details.html',
        patient=patient,
        medical_records=medical_records
    )

@doctor_bp.route('/consult/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def consult_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        notes = request.form.get('notes')
        medications = request.form.get('medications')
        instructions = request.form.get('instructions')
        
        report_file = request.files.get('report')
        report_filename = None
        if report_file and allowed_file(report_file.filename):
            report_filename = secure_filename(report_file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            report_file.save(os.path.join(upload_folder, report_filename))

        medical_record = MedicalRecord(
            patient_id=patient_id,
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes,
            report_file=report_filename
        )
        db.session.add(medical_record)
        db.session.flush()
        
        if medications:
            try:
                medications_json = json.loads(medications)
            except json.JSONDecodeError:
                flash('Invalid format for medications. Please use JSON.', 'danger')
                return redirect(url_for('doctor.consult_patient', patient_id=patient_id))

            prescription = Prescription(
                medical_record_id=medical_record.id,
                patient_id=patient_id,
                doctor_id=current_user.id,
                medications=medications_json,
                instructions=instructions
            )
            db.session.add(prescription)
        
        queue_service.remove_from_queue(patient_id)
        
        queue_entry = QueueEntry.query.filter_by(
            patient_id=patient_id,
            doctor_id=current_user.id,
            status='waiting'
        ).first()
        
        if queue_entry:
            queue_entry.status = 'completed'
            queue_entry.completed_at = datetime.utcnow()
        
        db.session.commit()
        # notify patient and update doctor queue in real-time
        try:
            socketio.emit('consultation:completed', {
                'patient_id': patient_id,
                'doctor_id': current_user.id,
                'medical_record_id': medical_record.id
            }, room=f'user_{patient_id}')

            # update doctor queue
            socketio.emit('queue:update', {'doctor_id': current_user.id, 'queue': queue_service.get_queue(current_user.id)}, room=f'doctor_{current_user.id}')
        except Exception:
            pass

        flash('Consultation completed successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))
    
    medical_history = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    return render_template(
        'doctor/consult.html',
        patient=patient,
        medical_history=medical_history
    )

@doctor_bp.route('/queue-data')
@login_required
@doctor_required
def queue_data():
    queue_list = queue_service.get_queue(current_user.id)
    active_queue_entries = []
    for queue_item in queue_list:
        patient = User.query.get(queue_item['patient_id'])
        if patient:
            # Convert to dict for JSON serialization
            item = queue_item.copy()
            item['patient_name'] = patient.full_name
            item['patient_email'] = patient.email
            item['patient_phone'] = patient.phone or 'N/A'
            active_queue_entries.append(item)
            
    return jsonify({'queue': active_queue_entries})

@doctor_bp.route('/call-next')
@login_required
@doctor_required
def call_next_patient():
    next_patient = queue_service.dequeue(current_user.id)
    
    if next_patient:
        queue_entry = QueueEntry.query.filter_by(
            patient_id=next_patient['patient_id'],
            doctor_id=current_user.id,
            status='waiting'
        ).first()
        
        if queue_entry:
            queue_entry.status = 'in_consultation'
            queue_entry.called_at = datetime.utcnow()
            db.session.commit()
        # notify the patient that they have been called
        try:
            pid = next_patient['patient_id']
            socketio.emit('patient:called', {
                'patient_id': pid,
                'doctor_id': current_user.id
            }, room=f'user_{pid}')
        except Exception:
            pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Next patient called.', 'patient': next_patient})

        flash(f'Next patient called.', 'info')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'No patients in queue.'})
        flash('No patients in queue.', 'warning')
    
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/prescription/<int:prescription_id>/download')
@login_required
@doctor_required
def download_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if prescription.doctor_id != current_user.id and prescription.patient_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "MediQueue - Medical Prescription")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Date: {prescription.created_at.strftime('%Y-%m-%d')}")
    p.drawString(100, 700, f"Doctor: Dr. {prescription.doctor.full_name}")
    p.drawString(100, 680, f"Patient: {prescription.patient.full_name}")
    
    p.drawString(100, 650, "Medications:")
    y = 630
    for med in prescription.medications:
        p.drawString(120, y, f"- {med['medication']} ({med['dosage']}) - {med['frequency']}")
        y -= 20

    p.drawString(100, y - 20, "Instructions:")
    p.drawString(120, y - 40, str(prescription.instructions))
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'prescription_{prescription_id}.pdf', mimetype='application/pdf')

@doctor_bp.route('/report/<int:record_id>/download')
@login_required
def download_report(record_id):
    medical_record = MedicalRecord.query.get_or_404(record_id)

    if current_user.id not in [medical_record.patient_id, medical_record.doctor_id]:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    if not medical_record.report_file:
        flash('No report available for this record.', 'warning')
        return redirect(request.referrer or url_for('main.index'))

    return send_file(
        os.path.join(current_app.config['UPLOAD_FOLDER'], medical_record.report_file),
        as_attachment=True
    )

@doctor_bp.route('/availability', methods=['GET', 'POST'])
@login_required
@doctor_required
def availability():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            slot_id = request.form.get('slot_id')
            if slot_id:
                slot = DoctorAvailability.query.get_or_404(slot_id)
                if slot.doctor_id == current_user.id:
                    db.session.delete(slot)
                    db.session.commit()
                    flash('Availability slot removed.', 'success')
                else:
                    flash('Access denied.', 'danger')
                return redirect(url_for('doctor.availability'))
        else:
            # Adding new availability
            day = int(request.form.get('day_of_week'))
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            is_available = request.form.get('is_available') == 'on'

            try:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                # Validate times
                if start_time >= end_time:
                    flash('End time must be after start time.', 'danger')
                    return redirect(url_for('doctor.availability'))
                
                # Check for overlapping slots
                overlapping = DoctorAvailability.query.filter(
                    DoctorAvailability.doctor_id == current_user.id,
                    DoctorAvailability.day_of_week == day,
                    db.or_(
                        db.and_(DoctorAvailability.start_time <= start_time, DoctorAvailability.end_time > start_time),
                        db.and_(DoctorAvailability.start_time < end_time, DoctorAvailability.end_time >= end_time)
                    )
                ).first()
                
                if overlapping:
                    flash('This time slot overlaps with an existing schedule.', 'danger')
                    return redirect(url_for('doctor.availability'))
                
                entry = DoctorAvailability(
                    doctor_id=current_user.id,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=is_available
                )
                db.session.add(entry)
                db.session.commit()
                flash('Availability added successfully.', 'success')
                
            except ValueError:
                flash('Invalid time format.', 'danger')
            except Exception as e:
                flash(f'Error adding availability: {str(e)}', 'danger')
                
            return redirect(url_for('doctor.availability'))

    # GET -> show availability sorted by day and time
    availability = DoctorAvailability.query.filter_by(doctor_id=current_user.id)\
        .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)\
        .all()
    return render_template('doctor/availability.html', availability=availability)
