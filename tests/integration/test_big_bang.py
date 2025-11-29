"""
Big Bang Integration Tests
Tests entire system integration without stubs or mocks.
"""
import pytest
from models import db, User, Department, Appointment, QueueEntry, MedicalRecord, Prescription, DoctorAvailability
from services import QueueService
from datetime import datetime, timedelta


class TestBigBangIntegration:
    """Big Bang integration tests - full system integration."""
    
    def test_complete_patient_journey(self, test_app, client):
        """Test: Registration -> Login -> Book Appointment -> Join Queue -> Consultation"""
        # Step 1: Registration
        response = client.post('/auth/register', data={
            'email': 'journey@test.com',
            'password': 'pass123',
            'full_name': 'Journey Patient',
            'phone': '1234567890',
            'age': '30',
            'gender': 'Male'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: Login
        response = client.post('/auth/login', data={
            'email': 'journey@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        assert response.status_code == 302
        
        # Step 3: Access dashboard
        response = client.get('/patient/dashboard', follow_redirects=True)
        assert response.status_code == 200
        
        # Step 4: Set up doctor and department
        with test_app.app_context():
            admin = User(
                email='admin@journey.com',
                full_name='Admin',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            dept = Department(name='General Medicine', description='General', is_active=True)
            db.session.add(dept)
            db.session.commit()
            
            doctor = User(
                email='doctor@journey.com',
                full_name='Dr. Journey',
                role='doctor',
                department_id=dept.id,
                specialization='General',
                avg_consultation_time=15
            )
            doctor.set_password('doctor123')
            db.session.add(doctor)
            db.session.commit()
            
            # Set availability
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                day_of_week=0,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                is_available=True
            )
            db.session.add(availability)
            db.session.commit()
            
            patient = User.query.filter_by(email='journey@test.com').first()
            
            # Step 5: Book appointment
            future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                department_id=dept.id,
                appointment_type='scheduled',
                appointment_date=datetime.strptime(f"{future_date} 10:00", '%Y-%m-%d %H:%M'),
                slot_time='10:00',
                status='scheduled',
                symptoms='Headache'
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Step 6: Join queue
            queue_service = QueueService()
            queue_service.enqueue(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_id=appointment.id
            )
            
            # Step 7: Verify queue position
            position = queue_service.get_position(patient.id)
            assert position is not None
            
            # Step 8: Create medical record (consultation)
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_id=appointment.id,
                symptoms='Headache',
                diagnosis='Migraine',
                notes='Prescribed medication'
            )
            db.session.add(record)
            db.session.commit()
            
            # Step 9: Create prescription
            prescription = Prescription(
                medical_record_id=record.id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                medications=[{'name': 'Paracetamol', 'dosage': '500mg'}],
                instructions='Take twice daily'
            )
            db.session.add(prescription)
            db.session.commit()
            
            # Verify complete integration
            assert appointment.id is not None
            assert record.id is not None
            assert prescription.id is not None
    
    def test_admin_doctor_patient_workflow(self, test_app, client):
        """Test: Admin creates doctor -> Doctor sets availability -> Patient books -> Queue works"""
        # Step 1: Admin creates department
        with test_app.app_context():
            admin = User(email='admin@workflow.com', full_name='Admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            dept = Department(name='Cardiology', description='Heart', is_active=True)
            db.session.add(dept)
            db.session.commit()
            
            # Step 2: Admin creates doctor
            doctor = User(
                email='doctor@workflow.com',
                full_name='Dr. Workflow',
                role='doctor',
                department_id=dept.id,
                specialization='Cardiology',
                avg_consultation_time=20
            )
            doctor.set_password('doctor123')
            db.session.add(doctor)
            db.session.commit()
            
            # Step 3: Doctor sets availability
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                day_of_week=0,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                is_available=True
            )
            db.session.add(availability)
            db.session.commit()
            
            # Step 4: Patient registers
            response = client.post('/auth/register', data={
                'email': 'patient@workflow.com',
                'password': 'pass123',
                'full_name': 'Workflow Patient',
                'phone': '1234567890'
            }, follow_redirects=True)
            
            # Step 5: Patient logs in
            response = client.post('/auth/login', data={
                'email': 'patient@workflow.com',
                'password': 'pass123'
            }, follow_redirects=False)
            
            # Step 6: Patient books appointment
            patient = User.query.filter_by(email='patient@workflow.com').first()
            future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                department_id=dept.id,
                appointment_type='scheduled',
                appointment_date=datetime.strptime(f"{future_date} 10:00", '%Y-%m-%d %H:%M'),
                slot_time='10:00',
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Step 7: Queue service integration
            queue_service = QueueService()
            queue_service.enqueue(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_id=appointment.id
            )
            
            # Verify all components work together
            queue = queue_service.get_queue(doctor.id)
            assert len(queue) == 1
            assert queue[0]['patient_id'] == patient.id
    
    def test_multi_user_queue_system(self, test_app):
        """Test: Multiple patients, multiple doctors, queue management"""
        with test_app.app_context():
            # Create multiple doctors
            dept = Department(name='Multi Test', description='Test', is_active=True)
            db.session.add(dept)
            db.session.commit()
            
            doctor1 = User(
                email='doctor1@multi.com',
                full_name='Dr. One',
                role='doctor',
                department_id=dept.id,
                avg_consultation_time=15
            )
            doctor1.set_password('pass123')
            db.session.add(doctor1)
            
            doctor2 = User(
                email='doctor2@multi.com',
                full_name='Dr. Two',
                role='doctor',
                department_id=dept.id,
                avg_consultation_time=20
            )
            doctor2.set_password('pass123')
            db.session.add(doctor2)
            db.session.commit()
            
            # Create multiple patients
            patients = []
            for i in range(5):
                patient = User(
                    email=f'patient{i}@multi.com',
                    full_name=f'Patient {i}',
                    role='patient'
                )
                patient.set_password('pass123')
                db.session.add(patient)
                patients.append(patient)
            db.session.commit()
            
            # Add patients to queues
            queue_service = QueueService()
            for i, patient in enumerate(patients):
                doctor_id = doctor1.id if i % 2 == 0 else doctor2.id
                queue_service.enqueue(
                    patient_id=patient.id,
                    doctor_id=doctor_id
                )
            
            # Verify queues
            queue1 = queue_service.get_queue(doctor1.id)
            queue2 = queue_service.get_queue(doctor2.id)
            
            assert len(queue1) == 3  # Patients 0, 2, 4
            assert len(queue2) == 2  # Patients 1, 3
            
            # Verify positions
            position = queue_service.get_position(patients[0].id)
            assert position is not None
            assert position['doctor_id'] == doctor1.id

