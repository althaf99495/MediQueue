#!/usr/bin/env python3
"""
Database initialization script for MediQueue.
Creates the database tables and populates them with default users.
"""

from app import create_app
from extensions import db
from models import User, Doctor, Patient
from datetime import date

def init_database():
    """Initialize database with tables and default data."""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin user already exists
        if User.query.filter_by(username='admin').first():
            print("Database already initialized with default users.")
            return
        
        print("Creating default users...")
        
        # Create Admin user
        admin_user = User(
            username='admin',
            email='admin@mediqueue.com',
            first_name='System',
            last_name='Administrator',
            phone='+1-555-0001',
            role='admin',
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create Doctor user
        doctor_user = User(
            username='doctor',
            email='doctor@mediqueue.com',
            first_name='John',
            last_name='Smith',
            phone='+1-555-0002',
            role='doctor',
            is_active=True
        )
        doctor_user.set_password('doctor123')
        db.session.add(doctor_user)
        
        # Create Receptionist user
        receptionist_user = User(
            username='receptionist',
            email='receptionist@mediqueue.com',
            first_name='Jane',
            last_name='Doe',
            phone='+1-555-0003',
            role='receptionist',
            is_active=True
        )
        receptionist_user.set_password('receptionist123')
        db.session.add(receptionist_user)
        
        # Commit users first to get their IDs
        db.session.commit()
        
        print("Creating doctor profile...")
        
        # Create Doctor profile
        doctor_profile = Doctor(
            user_id=doctor_user.id,
            license_number='MD123456',
            specialization='General Medicine',
            qualification='MBBS, MD',
            experience_years=10,
            consultation_fee=75.0,
            availability_status='available'
        )
        db.session.add(doctor_profile)
        
        # Create sample patients for demonstration
        print("Creating sample patients...")
        
        sample_patients = [
            {
                'patient_id': 'P000001',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'date_of_birth': date(1985, 6, 15),
                'gender': 'female',
                'phone': '+1-555-1001',
                'email': 'alice.johnson@email.com',
                'blood_type': 'A+',
                'address': '123 Main St, Anytown, ST 12345'
            },
            {
                'patient_id': 'P000002',
                'first_name': 'Bob',
                'last_name': 'Williams',
                'date_of_birth': date(1978, 11, 22),
                'gender': 'male',
                'phone': '+1-555-1002',
                'email': 'bob.williams@email.com',
                'blood_type': 'O-',
                'address': '456 Oak Ave, Anytown, ST 12345'
            },
            {
                'patient_id': 'P000003',
                'first_name': 'Carol',
                'last_name': 'Brown',
                'date_of_birth': date(1992, 3, 8),
                'gender': 'female',
                'phone': '+1-555-1003',
                'email': 'carol.brown@email.com',
                'blood_type': 'B+',
                'address': '789 Pine Rd, Anytown, ST 12345'
            }
        ]
        
        for patient_data in sample_patients:
            patient = Patient(**patient_data)
            db.session.add(patient)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\n" + "="*50)
        print("DEFAULT LOGIN CREDENTIALS:")
        print("="*50)
        print("Admin:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nDoctor:")
        print("  Username: doctor")
        print("  Password: doctor123")
        print("\nReceptionist:")
        print("  Username: receptionist")
        print("  Password: receptionist123")
        print("="*50)

if __name__ == '__main__':
    init_database()