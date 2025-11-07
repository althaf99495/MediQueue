from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    specialization = db.Column(db.String(100))
    consultation_fee = db.Column(db.Float, default=0.0)
    avg_consultation_time = db.Column(db.Integer, default=15)
    
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_doctor(self):
        return self.role == 'doctor'
    
    def is_patient(self):
        return self.role == 'patient'

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doctors = db.relationship('User', backref='department', lazy=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    appointment_type = db.Column(db.String(20), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    slot_time = db.Column(db.String(20))
    
    status = db.Column(db.String(20), default='scheduled')
    priority = db.Column(db.Integer, default=0)
    
    symptoms = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_appointments')
    department = db.relationship('Department', backref='appointments')

class QueueEntry(db.Model):
    __tablename__ = 'queue_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    queue_position = db.Column(db.Integer)
    status = db.Column(db.String(20), default='waiting')
    priority = db.Column(db.Integer, default=0)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    called_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='queue_entries')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_queue')
    appointment = db.relationship('Appointment', backref='queue_entry')

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    vital_signs = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='medical_records')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='records_created')
    appointment = db.relationship('Appointment', backref='medical_record')

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    medications = db.Column(db.JSON)
    instructions = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    medical_record = db.relationship('MedicalRecord', backref='prescriptions')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='prescriptions')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='prescriptions_written')

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    doctor = db.relationship('User', backref='availability_schedule')
