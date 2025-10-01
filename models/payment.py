from extensions import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(50), unique=True, nullable=False)  # Custom payment ID
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, insurance, other
    payment_type = db.Column(db.String(50), default='consultation')  # consultation, procedure, medication, other
    status = db.Column(db.String(20), default='pending')  # pending, paid, refunded, cancelled
    description = db.Column(db.Text)
    discount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    receipt_number = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # user who processed payment
    
    # Relationships
    doctor = db.relationship('Doctor', backref='payments_received', lazy=True)
    queue_entry = db.relationship('Queue', backref='payment', uselist=False, lazy=True)
    processor = db.relationship('User', backref='payments_processed', lazy=True)
    
    @property
    def final_amount(self):
        """Calculate final amount after discount and tax."""
        return self.amount - self.discount + self.tax_amount
    
    def __repr__(self):
        return f'<Payment {self.payment_id} - {self.total_amount} - {self.status}>'