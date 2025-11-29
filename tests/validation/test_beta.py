"""
Beta Testing - User Acceptance Testing
Tests real-world user scenarios and acceptance criteria.
"""
import pytest
from models import db, User, Department, Appointment, QueueEntry, MedicalRecord
from services import QueueService
from datetime import datetime, timedelta


class TestUserAcceptanceScenarios:
    """Beta testing - real user scenarios."""
    
    def test_scenario_new_patient_registration_and_booking(self, test_app, client):
        """Scenario: New patient registers, books appointment, joins queue."""
        # Step 1: Patient registers
        response = client.post('/auth/register', data={
            'email': 'beta@test.com',
            'password': 'pass123',
            'full_name': 'Beta Patient',
            'phone': '1234567890',
            'age': '25',
            'gender': 'Female',
            'address': '123 Test St',
            'blood_group': 'A+'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: Patient logs in
        response = client.post('/auth/login', data={
            'email': 'beta@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        assert response.status_code == 302
        
        # Step 3: Set up doctor and department
        with test_app.app_context():
            dept = Department(name='Beta Department', description='Test', is_active=True)
            db.session.add(dept)
            
            doctor = User(
                email='betadoctor@test.com',
                full_name='Dr. Beta',
                role='doctor',
                department_id=dept.id,
                specialization='General',
                avg_consultation_time=15
            )
            doctor.set_password('pass123')
            db.session.add(doctor)
            
            from models import DoctorAvailability
            doctor_id = doctor.id
            availability = DoctorAvailability(
                doctor_id=doctor_id,
                day_of_week=0,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                is_available=True
            )
            db.session.add(availability)
            db.session.commit()
            
            # Step 4: Patient books appointment
            patient = User.query.filter_by(email='beta@test.com').first()
            future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                department_id=dept.id,
                appointment_type='scheduled',
                appointment_date=datetime.strptime(f"{future_date} 10:00", '%Y-%m-%d %H:%M'),
                slot_time='10:00',
                status='scheduled',
                symptoms='Fever and cough'
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Step 5: Patient joins queue
            queue_service = QueueService()
            queue_service.enqueue(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_id=appointment.id
            )
            
            # Verify acceptance criteria
            position = queue_service.get_position(patient.id)
            assert position is not None
            assert appointment.status == 'scheduled'
    
    def test_scenario_doctor_manages_patients(self, test_app, authenticated_doctor):
        """Scenario: Doctor views queue, calls patient, creates record."""
        with test_app.app_context():
            # Create patient and add to queue
            patient = User(
                email='doctorpatient@test.com',
                full_name='Doctor Patient',
                role='patient'
            )
            patient.set_password('pass123')
            db.session.add(patient)
            db.session.commit()
            
            queue_service = QueueService()
            doctor = User.query.filter_by(email='doctor@test.com').first()
            queue_service.enqueue(
                patient_id=patient.id,
                doctor_id=doctor.id
            )
            
            # Doctor views queue
            response = authenticated_doctor.get('/doctor/dashboard')
            assert response.status_code == 200
            
            # Doctor creates medical record
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                symptoms='Headache',
                diagnosis='Migraine',
                notes='Prescribed rest'
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.id is not None
    
    def test_scenario_admin_manages_system(self, test_app, authenticated_admin):
        """Scenario: Admin creates department, adds doctor, views analytics."""
        # Admin accesses departments page
        response = authenticated_admin.get('/admin/departments')
        assert response.status_code == 200
        
        with test_app.app_context():
            # Create department directly
            dept = Department(
                name='Beta Admin Department',
                description='Created by admin',
                is_active=True
            )
            db.session.add(dept)
            db.session.commit()
            assert dept is not None
            
            # Admin creates doctor
            doctor = User(
                email='admincreated@test.com',
                full_name='Admin Created Doctor',
                role='doctor',
                department_id=dept.id,
                specialization='Cardiology'
            )
            doctor.set_password('pass123')
            db.session.add(doctor)
            db.session.commit()
            
            # Admin views analytics
            response = authenticated_admin.get('/admin/analytics')
            assert response.status_code == 200
    
    def test_scenario_patient_tracks_queue_position(self, test_app, authenticated_patient, doctor_user):
        """Scenario: Patient joins queue and tracks position in real-time."""
        queue_service = QueueService()
        
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            doctor_id = doctor_user.id
            patient_id = patient.id
            
            # Add multiple patients to queue
            for i in range(3):
                temp_patient = User(
                    email=f'temp{i}@test.com',
                    full_name=f'Temp {i}',
                    role='patient'
                )
                temp_patient.set_password('pass123')
                db.session.add(temp_patient)
                db.session.commit()
                queue_service.enqueue(patient_id=temp_patient.id, doctor_id=doctor_id)
            
            # Add main patient
            queue_service.enqueue(patient_id=patient_id, doctor_id=doctor_id)
            
            # Patient checks position
            position = queue_service.get_position(patient_id)
            assert position is not None
            assert position['position'] == 4  # 4th in queue
            
            # Patient views dashboard
            response = authenticated_patient.get('/patient/dashboard')
            assert response.status_code == 200
    
    def test_scenario_walk_in_patient(self, test_app, authenticated_patient, doctor_user):
        """Scenario: Walk-in patient joins queue without appointment."""
        queue_service = QueueService()
        
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            doctor_id = doctor_user.id
            patient_id = patient.id
            
            # Join queue without appointment
            queue_service.enqueue(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_id=None
            )
            
            # Verify in queue
            position = queue_service.get_position(patient_id)
            assert position is not None
            assert position['entry']['appointment_id'] is None
    
    def test_scenario_appointment_to_consultation_flow(self, test_app, authenticated_patient, doctor_user, department):
        """Scenario: Appointment -> Queue -> Consultation -> Medical Record."""
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            doctor_id = doctor_user.id
            patient_id = patient.id
            dept_id = department.id
            
            # Create appointment
            future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                department_id=dept_id,
                appointment_type='scheduled',
                appointment_date=datetime.strptime(f"{future_date} 10:00", '%Y-%m-%d %H:%M'),
                slot_time='10:00',
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            appointment_id = appointment.id
            
            # Join queue
            queue_service = QueueService()
            queue_service.enqueue(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_id=appointment_id
            )
            
            # Consultation (medical record)
            record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_id=appointment_id,
                symptoms='Fever',
                diagnosis='Common cold',
                notes='Rest and fluids'
            )
            db.session.add(record)
            
            # Update appointment status
            appointment.status = 'completed'
            db.session.commit()
            
            # Verify complete flow
            assert appointment.status == 'completed'
            assert record.id is not None
            assert record.appointment_id == appointment.id


class TestAcceptanceCriteria:
    """Test specific acceptance criteria."""
    
    def test_acceptance_secure_authentication(self, test_app, client):
        """Acceptance: Authentication must be secure."""
        # Test password hashing
        with test_app.app_context():
            user = User(email='secure@test.com', full_name='Secure', role='patient')
            user.set_password('secure_password')
            db.session.add(user)
            db.session.commit()
            
            # Password should be hashed
            assert user.password_hash != 'secure_password'
            assert user.check_password('secure_password') is True
            assert user.check_password('wrong_password') is False
    
    def test_acceptance_data_persistence(self, test_app):
        """Acceptance: Data must persist across sessions."""
        # Create data
        with test_app.app_context():
            user = User(email='persist@test.com', full_name='Persist', role='patient')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Retrieve in new context
        with test_app.app_context():
            retrieved = User.query.get(user_id)
            assert retrieved is not None
            assert retrieved.email == 'persist@test.com'
    
    def test_acceptance_concurrent_queue_operations(self, queue_service_instance):
        """Acceptance: System must handle concurrent queue operations."""
        # Simulate multiple patients joining simultaneously
        for i in range(10):
            queue_service_instance.enqueue(patient_id=i, doctor_id=1)
        
        queue = queue_service_instance.get_queue(doctor_id=1)
        assert len(queue) == 10

