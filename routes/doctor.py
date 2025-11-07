from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Prescription, Department
from services import QueueService
from datetime import datetime, timedelta
from functools import wraps
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

doctor_bp = Blueprint('doctor', __name__)
queue_service = QueueService()

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_doctor():
            flash('Access denied. Doctor privileges required.', 'danger')
            return redirect(url_for('index'))
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
        
        medical_record = MedicalRecord(
            patient_id=patient_id,
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes
        )
        db.session.add(medical_record)
        db.session.flush()
        
        if medications:
            prescription = Prescription(
                medical_record_id=medical_record.id,
                patient_id=patient_id,
                doctor_id=current_user.id,
                medications=medications,
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
        
        flash('Consultation completed successfully!', 'success')
        return redirect(url_for('doctor.dashboard'))
    
    medical_history = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    return render_template(
        'doctor/consult.html',
        patient=patient,
        medical_history=medical_history
    )

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
        
        flash(f'Next patient called.', 'info')
    else:
        flash('No patients in queue.', 'warning')
    
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/prescription/<int:prescription_id>/download')
@login_required
@doctor_required
def download_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if prescription.doctor_id != current_user.id:
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
    p.drawString(100, 630, str(prescription.medications))
    
    p.drawString(100, 600, "Instructions:")
    p.drawString(100, 580, str(prescription.instructions))
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'prescription_{prescription_id}.pdf', mimetype='application/pdf')
