
import sys
import os
from datetime import datetime

# Add the current directory to the path so we can import the app
sys.path.append(os.getcwd())

from app import app
from models import db, User, Payment, Appointment, Department

def verify_payment_implementation():
    print("Verifying Payment Implementation...")
    
    with app.app_context():
        # 1. Verify Payment Model exists
        try:
            # Create the table if it doesn't exist (since we didn't run migrations)
            db.create_all()
            print("Database tables updated/verified.")
        except Exception as e:
            print(f"Error updating database: {e}")
            return

        # 2. Create a test patient and appointment if needed
        patient = User.query.filter_by(role='patient').first()
        if not patient:
            print("No patient found. Creating a test patient.")
            patient = User(
                email='test_patient_payment@example.com',
                full_name='Test Patient Payment',
                role='patient'
            )
            patient.set_password('password')
            db.session.add(patient)
            db.session.commit()
            
        print(f"Using patient: {patient.full_name} (ID: {patient.id})")
        
        # 3. Create a test payment
        print("Creating a test payment...")
        payment = Payment(
            patient_id=patient.id,
            amount=150.00,
            payment_method='card',
            status='completed',
            transaction_id='TXN-TEST-001',
            notes='Test payment verification'
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            print(f"Payment created successfully. ID: {payment.id}")
        except Exception as e:
            print(f"Error creating payment: {e}")
            return
            
        # 4. Verify retrieval
        retrieved_payment = Payment.query.get(payment.id)
        if retrieved_payment:
            print(f"Verified payment retrieval: ${retrieved_payment.amount} - {retrieved_payment.status}")
        else:
            print("Failed to retrieve payment.")
            
        # 5. Clean up
        print("Cleaning up test data...")
        db.session.delete(payment)
        # Don't delete the patient as it might be used by other tests or was existing
        if patient.email == 'test_patient_payment@example.com':
             db.session.delete(patient)
        db.session.commit()
        print("Verification complete.")

if __name__ == "__main__":
    verify_payment_implementation()
