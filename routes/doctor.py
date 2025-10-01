from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import Doctor, Patient, Queue, Prescription
from extensions import db
from .forms import PrescriptionForm
from .decorators import doctor_required

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Doctor dashboard with patient queue and statistics."""
    # Get doctor profile
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if not doctor:
        flash('Doctor profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get today's queue for this doctor
    today_queue = db.session.query(Queue, Patient).join(
        Patient, Queue.patient_id == Patient.id
    ).filter(
        Queue.doctor_id == doctor.id,
        db.func.date(Queue.created_at) == datetime.utcnow().date(),
        Queue.status.in_(['waiting', 'in_progress'])
    ).order_by(Queue.queue_number.asc()).all()
    
    # Statistics
    total_patients_today = Queue.query.filter(
        Queue.doctor_id == doctor.id,
        db.func.date(Queue.created_at) == datetime.utcnow().date()
    ).count()
    
    completed_today = Queue.query.filter(
        Queue.doctor_id == doctor.id,
        db.func.date(Queue.created_at) == datetime.utcnow().date(),
        Queue.status == 'completed'
    ).count()
    
    return render_template('dashboard_doctor.html',
                         doctor=doctor,
                         today_queue=today_queue,
                         total_patients_today=total_patients_today,
                         completed_today=completed_today)

@doctor_bp.route('/prescriptions')
@login_required
@doctor_required
def view_prescriptions():
    """View all prescriptions created by this doctor."""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    prescriptions = db.session.query(Prescription, Patient).join(
        Patient, Prescription.patient_id == Patient.id
    ).filter(
        Prescription.doctor_id == doctor.id
    ).order_by(Prescription.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('view_prescriptions.html', prescriptions=prescriptions)

@doctor_bp.route('/prescriptions/add', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_prescription():
    """Add new prescription."""
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    form = PrescriptionForm()
    
    # Populate patient choices
    patients = Patient.query.all()
    form.patient_id.choices = [(p.id, f"{p.patient_id} - {p.full_name}") for p in patients]
    
    if form.validate_on_submit():
        # Generate prescription ID
        prescription_count = Prescription.query.count() + 1
        prescription_id = f"RX{prescription_count:06d}"
        
        prescription = Prescription(
            prescription_id=prescription_id,
            patient_id=form.patient_id.data,
            doctor_id=doctor.id,
            diagnosis=form.diagnosis.data,
            symptoms=form.symptoms.data,
            medications=form.medications.data,
            dosage_instructions=form.dosage_instructions.data,
            duration=form.duration.data,
            special_instructions=form.special_instructions.data,
            follow_up_date=form.follow_up_date.data,
            follow_up_notes=form.follow_up_notes.data,
            lab_tests=form.lab_tests.data,
            referrals=form.referrals.data
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        flash(f'Prescription {prescription_id} created successfully!', 'success')
        return redirect(url_for('doctor.view_prescriptions'))
    
    return render_template('prescription.html', form=form, title='Add Prescription')

@doctor_bp.route('/queue/call/<int:queue_id>')
@login_required
@doctor_required
def call_patient(queue_id):
    """Call next patient from queue."""
    queue_entry = Queue.query.get_or_404(queue_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if queue_entry.doctor_id != doctor.id:
        flash('You can only call patients assigned to you.', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    queue_entry.status = 'in_progress'
    queue_entry.called_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Patient {queue_entry.patient.full_name} has been called.', 'success')
    
    return redirect(url_for('doctor.dashboard'))

@doctor_bp.route('/queue/complete/<int:queue_id>')
@login_required
@doctor_required
def complete_consultation(queue_id):
    """Mark consultation as completed."""
    queue_entry = Queue.query.get_or_404(queue_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if queue_entry.doctor_id != doctor.id:
        flash('You can only complete consultations for your patients.', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    queue_entry.status = 'completed'
    queue_entry.completed_at = datetime.utcnow()
    
    # Calculate actual wait time
    if queue_entry.called_at and queue_entry.created_at:
        wait_time = (queue_entry.called_at - queue_entry.created_at).total_seconds() / 60
        queue_entry.actual_wait_time = int(wait_time)
    
    db.session.commit()
    flash(f'Consultation for {queue_entry.patient.full_name} marked as completed.', 'success')
    
    return redirect(url_for('doctor.dashboard'))