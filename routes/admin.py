from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Department
from services import QueueService
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)
queue_service = QueueService()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_doctors = User.query.filter_by(role='doctor', is_active=True).count()
    total_patients = User.query.filter_by(role='patient', is_active=True).count()
    total_departments = Department.query.filter_by(is_active=True).count()
    
    today = datetime.utcnow().date()
    patients_served_today = QueueEntry.query.filter(
        QueueEntry.status == 'completed',
        func.date(QueueEntry.completed_at) == today
    ).count()
    
    active_queues = db.session.query(
        User.full_name,
        func.count(QueueEntry.id).label('queue_length')
    ).join(QueueEntry, User.id == QueueEntry.doctor_id).filter(
        QueueEntry.status == 'waiting'
    ).group_by(User.id, User.full_name).all()
    
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_departments=total_departments,
        patients_served_today=patients_served_today,
        active_queues=active_queues,
        recent_appointments=recent_appointments
    )

@admin_bp.route('/doctors')
@login_required
@admin_required
def manage_doctors():
    doctors = User.query.filter_by(role='doctor').all()
    departments = Department.query.all()
    return render_template('admin/doctors.html', doctors=doctors, departments=departments)

@admin_bp.route('/doctors/add', methods=['POST'])
@login_required
@admin_required
def add_doctor():
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    password = request.form.get('password')
    phone = request.form.get('phone')
    department_id = request.form.get('department_id')
    specialization = request.form.get('specialization')
    consultation_fee = request.form.get('consultation_fee', 0.0)
    avg_consultation_time = request.form.get('avg_consultation_time', 15)
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.manage_doctors'))
    
    doctor = User(
        email=email,
        full_name=full_name,
        phone=phone,
        role='doctor',
        department_id=department_id,
        specialization=specialization,
        consultation_fee=float(consultation_fee),
        avg_consultation_time=int(avg_consultation_time)
    )
    doctor.set_password(password)
    
    db.session.add(doctor)
    db.session.commit()
    
    flash('Doctor added successfully!', 'success')
    return redirect(url_for('admin.manage_doctors'))

@admin_bp.route('/doctors/<int:doctor_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    if not doctor.is_doctor():
        flash('Invalid doctor.', 'danger')
        return redirect(url_for('admin.manage_doctors'))
    
    doctor.is_active = False
    db.session.commit()
    
    flash('Doctor deactivated successfully!', 'success')
    return redirect(url_for('admin.manage_doctors'))

@admin_bp.route('/patients')
@login_required
@admin_required
def manage_patients():
    patients = User.query.filter_by(role='patient').all()
    return render_template('admin/patients.html', patients=patients)

@admin_bp.route('/departments')
@login_required
@admin_required
def manage_departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if Department.query.filter_by(name=name).first():
        flash('Department already exists.', 'danger')
        return redirect(url_for('admin.manage_departments'))
    
    department = Department(name=name, description=description)
    db.session.add(department)
    db.session.commit()
    
    flash('Department added successfully!', 'success')
    return redirect(url_for('admin.manage_departments'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    today = datetime.utcnow().date()
    last_7_days = today - timedelta(days=7)
    
    daily_stats = db.session.query(
        func.date(QueueEntry.completed_at).label('date'),
        func.count(QueueEntry.id).label('count')
    ).filter(
        QueueEntry.status == 'completed',
        QueueEntry.completed_at >= last_7_days
    ).group_by(func.date(QueueEntry.completed_at)).all()
    
    doctor_stats = db.session.query(
        User.full_name,
        func.count(QueueEntry.id).label('patients_served')
    ).join(QueueEntry, User.id == QueueEntry.doctor_id).filter(
        QueueEntry.status == 'completed',
        func.date(QueueEntry.completed_at) == today
    ).group_by(User.id, User.full_name).all()
    
    return render_template(
        'admin/analytics.html',
        daily_stats=daily_stats,
        doctor_stats=doctor_stats
    )
