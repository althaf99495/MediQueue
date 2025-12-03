from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, Response
from flask_login import login_required, current_user
from models import db, User, Appointment, QueueEntry, MedicalRecord, Department, DoctorAvailability, Prescription, Report, Payment
from services import QueueService
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func
import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

admin_bp = Blueprint('admin', __name__)
queue_service = QueueService()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('main.index'))
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
        Department.name.label('department'),
        func.count(QueueEntry.id).label('queue_length')
    ).join(QueueEntry, User.id == QueueEntry.doctor_id)\
     .outerjoin(Department, User.department_id == Department.id)\
     .filter(
        QueueEntry.status == 'waiting'
    ).group_by(User.id, User.full_name, Department.name).all()
    
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
    # Show only active doctors by default, or all if show_inactive parameter is set
    show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'
    search = request.args.get('search', '')
    
    query = User.query.filter_by(role='doctor')
    
    if not show_inactive:
        query = query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.specialization.ilike(f'%{search}%')
            )
        )
    
    doctors = query.all()
    departments = Department.query.all()
    return render_template('admin/doctors.html', doctors=doctors, departments=departments, show_inactive=show_inactive, search=search)

@admin_bp.route('/doctors/export')
@login_required
@admin_required
def export_doctors():
    doctors = User.query.filter_by(role='doctor').all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Department', 'Specialization', 'Consultation Fee', 'Avg Consultation Time', 'Status', 'Created At'])
    
    # Write data
    for doctor in doctors:
        writer.writerow([
            doctor.id,
            doctor.full_name,
            doctor.email,
            doctor.phone or '',
            doctor.department.name if doctor.department else '',
            doctor.specialization or '',
            doctor.consultation_fee or 0,
            doctor.avg_consultation_time or 15,
            'Active' if doctor.is_active else 'Inactive',
            doctor.created_at.strftime('%Y-%m-%d %H:%M:%S') if doctor.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=doctors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@admin_bp.route('/doctors/export-pdf')
@login_required
@admin_required
def export_doctors_pdf():
    doctors = User.query.filter_by(role='doctor').all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#14a9c5'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("MediQueue - Doctor List", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Create table data
    data = [['ID', 'Name', 'Email', 'Department', 'Specialization', 'Status']]
    
    for doctor in doctors:
        data.append([
            str(doctor.id),
            doctor.full_name,
            doctor.email,
            doctor.department.name if doctor.department else 'N/A',
            doctor.specialization or 'General',
            'Active' if doctor.is_active else 'Inactive'
        ])
    
    # Create table
    table = Table(data, colWidths=[0.5*inch, 1.5*inch, 1.8*inch, 1.2*inch, 1.2*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#14a9c5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'doctors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

@admin_bp.route('/doctors/add', methods=['POST'])
@login_required
@admin_required
def add_doctor():
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password')
        phone = data.get('phone')
        department_id = data.get('department_id')
        specialization = data.get('specialization')
        consultation_fee = data.get('consultation_fee', 0.0)
        avg_consultation_time = data.get('avg_consultation_time', 15)
    else:
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        phone = request.form.get('phone')
        department_id = request.form.get('department_id')
        specialization = request.form.get('specialization')
        consultation_fee = request.form.get('consultation_fee', 0.0)
        avg_consultation_time = request.form.get('avg_consultation_time', 15)
    
    # Sanitize inputs
    if not department_id:
        department_id = None
        
    try:
        consultation_fee = float(consultation_fee) if consultation_fee else 0.0
    except ValueError:
        consultation_fee = 0.0
        
    try:
        avg_consultation_time = int(avg_consultation_time) if avg_consultation_time else 15
    except ValueError:
        avg_consultation_time = 15
    
    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'success': False, 'message': 'Email already exists.'}), 400
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.manage_doctors'))
    
    doctor = User(
        email=email,
        full_name=full_name,
        phone=phone,
        role='doctor',
        department_id=department_id,
        specialization=specialization,
        consultation_fee=consultation_fee,
        avg_consultation_time=avg_consultation_time
    )
    doctor.set_password(password)
    
    try:
        db.session.add(doctor)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Doctor added successfully!'})
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin.manage_doctors'))
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error adding doctor: {str(e)}'}), 500
        flash(f'Error adding doctor: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_doctors'))

@admin_bp.route('/doctors/<int:doctor_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    if not doctor.is_doctor():
        return jsonify({'success': False, 'message': 'Invalid doctor.'}), 400
        
    if request.is_json:
        data = request.get_json()
        
        # Update fields
        if 'full_name' in data:
            doctor.full_name = data['full_name']
        if 'email' in data:
            # Check if email is taken by another user
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != doctor.id:
                return jsonify({'success': False, 'message': 'Email already in use.'}), 400
            doctor.email = data['email']
        if 'phone' in data:
            doctor.phone = data['phone']
        if 'department_id' in data:
            doctor.department_id = data['department_id'] or None
        if 'specialization' in data:
            doctor.specialization = data['specialization']
        if 'consultation_fee' in data:
            try:
                doctor.consultation_fee = float(data['consultation_fee'])
            except (ValueError, TypeError):
                pass
        if 'avg_consultation_time' in data:
            try:
                doctor.avg_consultation_time = int(data['avg_consultation_time'])
            except (ValueError, TypeError):
                pass
                
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Doctor updated successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error updating doctor: {str(e)}'}), 500
            
    return jsonify({'success': False, 'message': 'Invalid request format.'}), 400

@admin_bp.route('/doctors/<int:doctor_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    
    if not doctor.is_doctor():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Invalid doctor.'})
        flash('Invalid doctor.', 'danger')
        return redirect(url_for('admin.manage_doctors'))
    
    # Always perform hard delete (permanent deletion) when delete button is clicked
    # The form always sends hard_delete=true now
    hard_delete = request.form.get('hard_delete', 'true').lower() == 'true'
    
    if hard_delete:
        # Check if doctor has any medical history that prevents hard deletion
        has_history = False
        
        # Check for medical records
        if MedicalRecord.query.filter_by(doctor_id=doctor_id).first():
            has_history = True
        # Check for prescriptions
        elif Prescription.query.filter_by(doctor_id=doctor_id).first():
            has_history = True
        # Check for reports
        elif Report.query.filter_by(doctor_id=doctor_id).first():
            has_history = True
            
        if has_history:
            # Soft delete - deactivate
            doctor.is_active = False
            
            # Cancel all upcoming appointments for this doctor
            upcoming_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.status == 'scheduled',
                Appointment.appointment_date >= datetime.utcnow()
            ).all()
            
            for appt in upcoming_appointments:
                appt.status = 'cancelled'
            
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Doctor cannot be permanently deleted due to existing medical history. Account has been deactivated instead.', 'action': 'deactivated'})
            flash('Doctor cannot be permanently deleted due to existing medical history. Account has been deactivated instead.', 'warning')
        else:
            # Hard delete - permanently remove from database
            # First, cancel all upcoming appointments
            upcoming_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.status == 'scheduled',
                Appointment.appointment_date >= datetime.utcnow()
            ).all()
            
            for appt in upcoming_appointments:
                appt.status = 'cancelled'
            
            # Remove from queue
            from services import QueueService
            queue_service = QueueService()
            queue_service.clear_queue(doctor_id)
            
            # Delete related records that should be removed
            try:
                # Delete queue entries
                QueueEntry.query.filter_by(doctor_id=doctor_id).delete()
                # Delete availability
                DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
                # Delete appointments (since we know there's no medical history, we can delete appointments too if we want, 
                # but usually we might want to keep them or cascade delete. 
                # However, Appointment has foreign key to User. 
                # If we want to hard delete the User, we MUST delete the appointments or set doctor_id to null.
                # Given the schema likely has NO cascade delete on Appointment.doctor_id, we must delete them.)
                Appointment.query.filter_by(doctor_id=doctor_id).delete()
                
                # Delete the doctor
                db.session.delete(doctor)
                db.session.commit()
                
                # Verify deletion by trying to query
                deleted_doctor = User.query.get(doctor_id)
                if deleted_doctor:
                    # If still exists, try to delete again
                    db.session.delete(deleted_doctor)
                    db.session.commit()
                
                flash('Doctor permanently deleted.', 'success')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'message': 'Doctor permanently deleted.', 'action': 'deleted'})
            except Exception as e:
                db.session.rollback()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'Error deleting doctor: {str(e)}'})
                flash(f'Error deleting doctor: {str(e)}. Please check database constraints.', 'danger')
                import traceback
                print(f"Delete error: {traceback.format_exc()}")
                return redirect(url_for('admin.manage_doctors'))
    else:
        # Soft delete - deactivate
        doctor.is_active = False
        
        # Cancel all upcoming appointments for this doctor
        upcoming_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == 'scheduled',
            Appointment.appointment_date >= datetime.utcnow()
        ).all()
        
        for appt in upcoming_appointments:
            appt.status = 'cancelled'
        
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Doctor deactivated and their upcoming appointments have been cancelled.', 'action': 'deactivated'})
        flash('Doctor deactivated and their upcoming appointments have been cancelled.', 'success')
    
    return redirect(url_for('admin.manage_doctors'))

@admin_bp.route('/patients')
@login_required
@admin_required
def manage_patients():
    search = request.args.get('search', '')
    if search:
        patients = User.query.filter(
            User.role == 'patient',
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%')
            )
        ).all()
    else:
        patients = User.query.filter_by(role='patient').all()
    return render_template('admin/patients.html', patients=patients, search=search)

@admin_bp.route('/patients/export')
@login_required
@admin_required
def export_patients():
    patients = User.query.filter_by(role='patient').all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Age', 'Gender', 'Blood Group', 'Address', 'Emergency Contact', 'Status', 'Created At'])
    
    # Write data
    for patient in patients:
        writer.writerow([
            patient.id,
            patient.full_name,
            patient.email,
            patient.phone or '',
            patient.age or '',
            patient.gender or '',
            patient.blood_group or '',
            patient.address or '',
            patient.emergency_contact or '',
            'Active' if patient.is_active else 'Inactive',
            patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if patient.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=patients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@admin_bp.route('/patients/export-pdf')
@login_required
@admin_required
def export_patients_pdf():
    patients = User.query.filter_by(role='patient').all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#14a9c5'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("MediQueue - Patient List", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Create table data
    data = [['ID', 'Name', 'Email', 'Phone', 'Age', 'Gender', 'Status']]
    
    for patient in patients:
        data.append([
            str(patient.id),
            patient.full_name,
            patient.email,
            patient.phone or 'N/A',
            str(patient.age) if patient.age else 'N/A',
            patient.gender or 'N/A',
            'Active' if patient.is_active else 'Inactive'
        ])
    
    # Create table
    table = Table(data, colWidths=[0.5*inch, 1.5*inch, 1.8*inch, 1*inch, 0.5*inch, 0.7*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#14a9c5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'patients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

@admin_bp.route('/departments')
@login_required
@admin_required
def manage_departments():
    search = request.args.get('search', '')
    if search:
        departments = Department.query.filter(
            db.or_(
                Department.name.ilike(f'%{search}%'),
                Department.description.ilike(f'%{search}%')
            )
        ).all()
    else:
        departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments, search=search)

@admin_bp.route('/departments/export')
@login_required
@admin_required
def export_departments():
    departments = Department.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Description', 'Status', 'Created At', 'Doctor Count'])
    
    # Write data
    for dept in departments:
        doctor_count = User.query.filter_by(role='doctor', department_id=dept.id, is_active=True).count()
        writer.writerow([
            dept.id,
            dept.name,
            dept.description or '',
            'Active' if dept.is_active else 'Inactive',
            dept.created_at.strftime('%Y-%m-%d %H:%M:%S') if dept.created_at else '',
            doctor_count
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=departments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@admin_bp.route('/departments/export-pdf')
@login_required
@admin_required
def export_departments_pdf():
    departments = Department.query.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#14a9c5'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("MediQueue - Department List", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Create table data
    data = [['ID', 'Name', 'Description', 'Doctors', 'Status']]
    
    for dept in departments:
        doctor_count = User.query.filter_by(role='doctor', department_id=dept.id, is_active=True).count()
        data.append([
            str(dept.id),
            dept.name,
            (dept.description or 'N/A')[:50],
            str(doctor_count),
            'Active' if dept.is_active else 'Inactive'
        ])
    
    # Create table
    table = Table(data, colWidths=[0.5*inch, 1.5*inch, 2.5*inch, 0.8*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#14a9c5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'departments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

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
    last_30_days = today - timedelta(days=30)
    
    # Daily stats for last 7 days
    daily_stats = db.session.query(
        func.date(QueueEntry.completed_at).label('date'),
        func.count(QueueEntry.id).label('count')
    ).filter(
        QueueEntry.status == 'completed',
        QueueEntry.completed_at >= last_7_days
    ).group_by(func.date(QueueEntry.completed_at)).all()
    
    # Doctor stats for today
    doctor_stats = db.session.query(
        User.full_name,
        func.count(QueueEntry.id).label('patients_served')
    ).join(QueueEntry, User.id == QueueEntry.doctor_id).filter(
        QueueEntry.status == 'completed',
        func.date(QueueEntry.completed_at) == today
    ).group_by(User.id, User.full_name).all()
    
    # Appointment statistics
    total_appointments = Appointment.query.count()
    scheduled_appointments = Appointment.query.filter_by(status='scheduled').count()
    completed_appointments = Appointment.query.filter_by(status='completed').count()
    cancelled_appointments = Appointment.query.filter_by(status='cancelled').count()
    
    # Monthly appointment trends (SQLite compatible)
    monthly_appointments = db.session.query(
        func.strftime('%Y-%m', Appointment.appointment_date).label('month'),
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.appointment_date >= last_30_days
    ).group_by(func.strftime('%Y-%m', Appointment.appointment_date)).all()
    
    # Department statistics
    dept_stats = db.session.query(
        Department.name,
        func.count(Appointment.id).label('appointment_count')
    ).join(Appointment, Department.id == Appointment.department_id).filter(
        Appointment.appointment_date >= last_30_days
    ).group_by(Department.id, Department.name).all()
    
    return render_template(
        'admin/analytics.html',
        daily_stats=daily_stats,
        doctor_stats=doctor_stats,
        total_appointments=total_appointments,
        scheduled_appointments=scheduled_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        monthly_appointments=monthly_appointments,
        dept_stats=dept_stats
    )

@admin_bp.route('/appointments')
@login_required
@admin_required
def manage_appointments():
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = Appointment.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.join(User, Appointment.patient_id == User.id).filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    appointments = query.order_by(Appointment.appointment_date.desc()).limit(100).all()
    
    return render_template(
        'admin/appointments.html',
        appointments=appointments,
        status_filter=status_filter,
        search=search
    )

@admin_bp.route('/patients/<int:patient_id>')
@login_required
@admin_required
def view_patient(patient_id):
    patient = User.query.get_or_404(patient_id)
    if not patient.is_patient():
        flash('User is not a patient.', 'danger')
        return redirect(url_for('admin.manage_patients'))
        
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appointment_date.desc()).all()
    medical_records = MedicalRecord.query.filter_by(patient_id=patient.id).order_by(MedicalRecord.visit_date.desc()).all()
    payments = Payment.query.filter_by(patient_id=patient.id).order_by(Payment.created_at.desc()).all()
    
    return render_template(
        'admin/patient_details.html',
        patient=patient,
        appointments=appointments,
        medical_records=medical_records,
        payments=payments
    )

@admin_bp.route('/payments')
@login_required
@admin_required
def manage_payments():
    search = request.args.get('search', '')
    
    query = Payment.query.join(User, Payment.patient_id == User.id)
    
    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                Payment.transaction_id.ilike(f'%{search}%')
            )
        )
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    # For the add payment modal
    patients = User.query.filter_by(role='patient', is_active=True).all()
    
    return render_template('admin/payments.html', payments=payments, patients=patients, search=search)

@admin_bp.route('/payments/add', methods=['POST'])
@login_required
@admin_required
def add_payment():
    patient_id = request.form.get('patient_id')
    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    status = request.form.get('status', 'completed')
    transaction_id = request.form.get('transaction_id')
    notes = request.form.get('notes')
    
    if not patient_id or not amount or not payment_method:
        flash('Missing required fields.', 'danger')
        return redirect(url_for('admin.manage_payments'))
        
    try:
        amount = float(amount)
    except ValueError:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('admin.manage_payments'))
        
    payment = Payment(
        patient_id=patient_id,
        amount=amount,
        payment_method=payment_method,
        status=status,
        transaction_id=transaction_id,
        notes=notes
    )
    
    try:
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'danger')
        
    return redirect(url_for('admin.manage_payments'))
