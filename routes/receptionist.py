from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from models import Patient, Queue, Payment, Doctor
from extensions import db
from .forms import PatientForm, PaymentForm
from .decorators import receptionist_required, admin_or_receptionist_required

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
@receptionist_required
def dashboard():
    """Receptionist dashboard with patient management."""
    # Get today's statistics
    today_patients = Patient.query.filter(
        db.func.date(Patient.created_at) == datetime.utcnow().date()
    ).count()
    
    today_queue = Queue.query.filter(
        db.func.date(Queue.created_at) == datetime.utcnow().date()
    ).count()
    
    today_payments = Payment.query.filter(
        db.func.date(Payment.created_at) == datetime.utcnow().date(),
        Payment.status == 'paid'
    ).count()
    
    # Recent activities
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    active_queue = Queue.query.filter(
        Queue.status.in_(['waiting', 'in_progress'])
    ).order_by(Queue.queue_number.asc()).limit(10).all()
    
    return render_template('dashboard_receptionist.html',
                         today_patients=today_patients,
                         today_queue=today_queue,
                         today_payments=today_payments,
                         recent_patients=recent_patients,
                         active_queue=active_queue)

@receptionist_bp.route('/patients')
@login_required
@admin_or_receptionist_required
def manage_patients():
    """Manage patients."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Patient.query
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.contains(search),
                Patient.last_name.contains(search),
                Patient.patient_id.contains(search),
                Patient.phone.contains(search)
            )
        )
    
    patients = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('manage_patients.html', patients=patients, search=search)

@receptionist_bp.route('/patients/register', methods=['GET', 'POST'])
@login_required
@admin_or_receptionist_required
def register_patient():
    """Register new patient."""
    form = PatientForm()
    
    if form.validate_on_submit():
        # Generate patient ID
        patient_count = Patient.query.count() + 1
        patient_id = f"P{patient_count:06d}"
        
        patient = Patient(
            patient_id=patient_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            emergency_contact=form.emergency_contact.data,
            emergency_phone=form.emergency_phone.data,
            blood_type=form.blood_type.data,
            allergies=form.allergies.data,
            medical_history=form.medical_history.data,
            insurance_info=form.insurance_info.data
        )
        
        db.session.add(patient)
        db.session.commit()
        
        flash(f'Patient {patient_id} registered successfully!', 'success')
        return redirect(url_for('receptionist.manage_patients'))
    
    return render_template('register_patient.html', form=form)

@receptionist_bp.route('/patients/search')
@login_required
@admin_or_receptionist_required
def search_patient():
    """Search patients."""
    query = request.args.get('query', '')
    
    if query:
        patients = Patient.query.filter(
            db.or_(
                Patient.first_name.contains(query),
                Patient.last_name.contains(query),
                Patient.patient_id.contains(query),
                Patient.phone.contains(query)
            )
        ).limit(10).all()
    else:
        patients = []
    
    return render_template('search_patient.html', patients=patients, query=query)

@receptionist_bp.route('/payments')
@login_required
@admin_or_receptionist_required
def manage_payments():
    """Manage payments."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    payments = db.session.query(Payment, Patient).join(
        Patient, Payment.patient_id == Patient.id
    ).order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('manage_payments.html', payments=payments)

@receptionist_bp.route('/payments/add', methods=['GET', 'POST'])
@login_required
@admin_or_receptionist_required
def add_payment():
    """Add new payment."""
    form = PaymentForm()
    
    # Populate choices
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    form.patient_id.choices = [(p.id, f"{p.patient_id} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [('', '-- Select Doctor --')] + [(d.id, f"Dr. {d.user.full_name}") for d in doctors]
    
    if form.validate_on_submit():
        # Generate payment ID
        payment_count = Payment.query.count() + 1
        payment_id = f"PAY{payment_count:06d}"
        receipt_number = f"RCP{payment_count:06d}"
        
        total_amount = form.amount.data - form.discount.data + form.tax_amount.data
        
        payment = Payment(
            payment_id=payment_id,
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data if form.doctor_id.data else None,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            payment_type=form.payment_type.data,
            description=form.description.data,
            discount=form.discount.data,
            tax_amount=form.tax_amount.data,
            total_amount=total_amount,
            receipt_number=receipt_number,
            status='paid',
            paid_at=datetime.utcnow(),
            processed_by=current_user.id
        )
        
        db.session.add(payment)
        db.session.commit()
        
        flash(f'Payment {payment_id} processed successfully!', 'success')
        return redirect(url_for('receptionist.manage_payments'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    payments = db.session.query(Payment, Patient).join(
        Patient, Payment.patient_id == Patient.id
    ).order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('manage_payments.html', form=form, title='Add Payment', payments=payments)