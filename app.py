from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
import os
from extensions import socketio

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from routes.auth import auth_bp
from routes.doctor import doctor_bp
from routes.patient import patient_bp
from routes.admin import admin_bp
from routes.setup import setup_bp

app.register_blueprint(auth_bp)
app.register_blueprint(doctor_bp, url_prefix='/doctor')
app.register_blueprint(patient_bp, url_prefix='/patient')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(setup_bp)

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_doctor():
            return redirect(url_for('doctor.dashboard'))
        elif current_user.is_patient():
            return redirect(url_for('patient.dashboard'))
    return render_template('index.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

with app.app_context():
    db.create_all()
    
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_email and admin_password:
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                email=admin_email,
                full_name='System Administrator',
                role='admin',
                phone=''
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account created: {admin_email}")
        else:
            print(f"Admin account already exists: {admin_email}")
    else:
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count == 0:
            print("\n" + "="*60)
            print("NO ADMIN ACCOUNT FOUND!")
            print("Please create an admin account by visiting /setup")
            print("Or set ADMIN_EMAIL and ADMIN_PASSWORD environment variables")
            print("="*60 + "\n")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# Socket.IO helpers for clients to join/leave rooms
from flask_socketio import join_room, leave_room


@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)


@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)
