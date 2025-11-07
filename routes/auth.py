from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is inactive. Please contact administration.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=True)
            next_page = request.args.get('next')
            
            if not next_page:
                if user.is_admin():
                    next_page = url_for('admin.dashboard')
                elif user.is_doctor():
                    next_page = url_for('doctor.dashboard')
                elif user.is_patient():
                    next_page = url_for('patient.dashboard')
                else:
                    next_page = url_for('index')
            
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        emergency_contact = request.form.get('emergency_contact')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role='patient',
            age=age,
            gender=gender,
            address=address,
            blood_group=blood_group,
            emergency_contact=emergency_contact
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))
