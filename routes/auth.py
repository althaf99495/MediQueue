from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User
from extensions import db
from .forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'receptionist':
            return redirect(url_for('receptionist.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect to appropriate dashboard
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'receptionist':
                return redirect(url_for('receptionist.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))