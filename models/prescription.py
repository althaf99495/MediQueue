from extensions import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.String(50), unique=True, nullable=False)  # Custom prescription ID
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'))
    
    # Prescription details
    diagnosis = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)
    medications = db.Column(db.Text, nullable=False)  # JSON string of medication list
    dosage_instructions = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(50))  # e.g., "7 days", "2 weeks"
    
    # Additional instructions
    special_instructions = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    follow_up_notes = db.Column(db.Text)
    
    # Lab tests and referrals
    lab_tests = db.Column(db.Text)  # JSON string of lab tests
    referrals = db.Column(db.Text)  # JSON string of referrals
    
    # Status and validation
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    is_valid = db.Column(db.Boolean, default=True)
    validation_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    queue_entry = db.relationship('Queue', backref='prescription', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Prescription {self.prescription_id} - Patient: {self.patient_id} - Doctor: {self.doctor_id}>'