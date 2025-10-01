from extensions import db
from datetime import datetime

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Float, default=0.0)
    availability_status = db.Column(db.String(20), default='available')  # available, busy, offline
    schedule = db.Column(db.Text)  # JSON string of weekly schedule
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    
    # Relationship with Prescriptions
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Doctor {self.license_number} - {self.specialization}>'