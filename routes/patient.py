from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Prescription, Department
from services import QueueService
from datetime import datetime, timedelta
from functools import wraps
import qrcode
import io
import base64

patient_bp = Blueprint('patient', __name__)
queue_service = QueueService()

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_patient():
            flash('Access denied. Patient account required.', 'danger')
            return redirect(url_for('index'))
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
    if queue_position:
        doctor = User.query.get(queue_position['doctor_id'])
        if doctor:
            estimated_wait = (queue_position['position'] - 1) * doctor.avg_consultation_time
    
    return render_template(
        'patient/dashboard.html',
        queue_position=queue_position,
        estimated_wait=estimated_wait,
        appointments=upcoming_appointments,
        medical_records=medical_records
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
        
        doctor = User.query.get(doctor_id)
        if not doctor or not doctor.is_doctor():
            flash('Invalid doctor selected.', 'danger')
            return redirect(url_for('patient.book_appointment'))
        
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            department_id=doctor.department_id,
            appointment_type='scheduled',
            appointment_date=datetime.strptime(f"{appointment_date} {slot_time}", '%Y-%m-%d %H:%M'),
            slot_time=slot_time,
            symptoms=symptoms,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
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
    
    flash('You have left the queue.', 'info')
    return redirect(url_for('patient.dashboard'))

@patient_bp.route('/medical-history')
@login_required
@patient_required
def medical_history():
    records = MedicalRecord.query.filter_by(
        patient_id=current_user.id
    ).order_by(MedicalRecord.visit_date.desc()).all()
    
    return render_template('patient/medical_history.html', records=records)

@patient_bp.route('/prescriptions')
@login_required
@patient_required
def prescriptions():
    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient/prescriptions.html', prescriptions=prescriptions)

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
