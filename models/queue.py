from extensions import db
from datetime import datetime

class Queue(db.Model):
    __tablename__ = 'queue'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    queue_number = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # normal, high, urgent
    status = db.Column(db.String(20), default='waiting')  # waiting, in_progress, completed, cancelled
    appointment_type = db.Column(db.String(50), default='consultation')
    notes = db.Column(db.Text)
    estimated_time = db.Column(db.Integer)  # estimated wait time in minutes
    actual_wait_time = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    called_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # receptionist who added to queue
    
    # Relationships
    doctor = db.relationship('Doctor', backref='queue_entries', lazy=True)
    creator = db.relationship('User', backref='queue_entries_created', lazy=True)
    
    def __repr__(self):
        return f'<Queue #{self.queue_number} - Patient: {self.patient_id} - Status: {self.status}>'