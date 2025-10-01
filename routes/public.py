from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from models import Queue, Patient
from extensions import db

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'receptionist':
            return redirect(url_for('receptionist.dashboard'))
    
    return redirect(url_for('auth.login'))

@public_bp.route('/queue-display')
def queue_display():
    """Public queue display for waiting room."""
    active_queue = db.session.query(Queue, Patient).join(
        Patient, Queue.patient_id == Patient.id
    ).filter(
        Queue.status.in_(['waiting', 'in_progress'])
    ).order_by(Queue.queue_number.asc()).all()
    
    return render_template('queue_display.html', queue_entries=active_queue)

@public_bp.route('/about')
def about():
    return render_template('about.html')