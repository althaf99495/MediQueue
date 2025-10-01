from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import User, Doctor, Patient, Queue, Payment, Prescription
from extensions import db
from .forms import UserForm, DoctorForm
from .decorators import admin_required
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask import make_response

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics."""
    # Get statistics
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_users = User.query.count()
    today_payments = Payment.query.filter(
        db.func.date(Payment.created_at) == datetime.utcnow().date()
    ).count()
    
    # Recent activities
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard_admin.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_users=total_users,
                         today_payments=today_payments,
                         recent_patients=recent_patients,
                         recent_payments=recent_payments)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage system users."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    users = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user."""
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data or 'password123')
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('edit_user.html', form=form, title='Add User')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user."""
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('edit_user.html', form=form, user=user, title='Edit User')

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate system reports."""
    # Get date range from request
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Generate report data
    payments_data = Payment.query.filter(
        Payment.created_at.between(start_date, end_date)
    ).all()
    
    patients_data = Patient.query.filter(
        Patient.created_at.between(start_date, end_date)
    ).all()
    
    return render_template('reports.html',
                         payments_data=payments_data,
                         patients_data=patients_data)
@admin_bp.route('/reports/download')
@login_required
@admin_required
def download_report():
    report_type = request.args.get('report_type', 'payments')
    report_format = request.args.get('format', 'csv')
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    if report_type == 'payments':
        data = Payment.query.filter(Payment.created_at.between(start_date, end_date)).all()
        df_data = [{
            'ID': p.id,
            'Patient': f"{p.patient.user.first_name} {p.patient.user.last_name}" if p.patient and p.patient.user else 'N/A',
            'Amount': p.amount,
            'Date': p.created_at.strftime('%Y-%m-%d')
        } for p in data]
        df = pd.DataFrame(df_data)
        filename = f"payments_report_{start_date}_to_{end_date}"

    elif report_type == 'patients':
        data = Patient.query.filter(Patient.created_at.between(start_date, end_date)).all()
        df_data = [{
            'ID': p.id,
            'Name': f"{p.user.first_name} {p.user.last_name}" if p.user else 'N/A',
            'Date Joined': p.created_at.strftime('%Y-%m-%d')
        } for p in data]
        df = pd.DataFrame(df_data)
        filename = f"patients_report_{start_date}_to_{end_date}"
    else:
        flash('Invalid report type.', 'danger')
        return redirect(url_for('admin.reports'))

    if report_format == 'csv':
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

    elif report_format == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.drawString(30, height - 50, f"{report_type.capitalize()} Report")
        p.drawString(30, height - 70, f"From: {start_date} To: {end_date}")

        y = height - 100
        # Table Header
        x_offset = 30
        for col in df.columns:
            p.drawString(x_offset, y, str(col))
            x_offset += 100
        y -= 20

        # Table Rows
        for index, row in df.iterrows():
            if y < 50: # New page
                p.showPage()
                y = height - 50
            x_offset = 30
            for item in row:
                p.drawString(x_offset, y, str(item))
                x_offset += 100
            y -= 20

        p.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response

    else:
        flash('Invalid format.', 'danger')
        return redirect(url_for('admin.reports'))