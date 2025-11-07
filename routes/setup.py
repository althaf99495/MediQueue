from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, User

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    admin_count = User.query.filter_by(role='admin').count()
    
    if admin_count > 0:
        flash('Admin account already exists. Please contact an existing administrator.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone', '')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('setup.setup'))
        
        admin = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role='admin'
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        flash('Admin account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('setup.html')
