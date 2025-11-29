"""
Unit Tests for Models
Tests individual model components and their methods.
"""
import pytest
from datetime import datetime, timedelta
from models import db, User, Department, Appointment, QueueEntry, MedicalRecord, Prescription, DoctorAvailability


class TestUserModel:
    """Unit tests for User model."""
    
    def test_user_creation(self, test_app):
        """Test creating a user."""
        with test_app.app_context():
            user = User(
                email='test@example.com',
                full_name='Test User',
                role='patient',
                phone='1234567890'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'test@example.com'
            assert user.full_name == 'Test User'
            assert user.role == 'patient'
    
    def test_password_hashing(self, test_app):
        """Test password hashing and verification."""
        with test_app.app_context():
            user = User(email='test@example.com', full_name='Test', role='patient')
            user.set_password('secure_password')
            db.session.add(user)
            db.session.commit()
            
            assert user.check_password('secure_password') is True
            assert user.check_password('wrong_password') is False
            assert user.password_hash != 'secure_password'
    
    def test_role_check_methods(self, test_app):
        """Test role checking methods."""
        with test_app.app_context():
            admin = User(email='admin@test.com', full_name='Admin', role='admin')
            doctor = User(email='doctor@test.com', full_name='Doctor', role='doctor')
            patient = User(email='patient@test.com', full_name='Patient', role='patient')
            
            assert admin.is_admin() is True
            assert admin.is_doctor() is False
            assert admin.is_patient() is False
            
            assert doctor.is_doctor() is True
            assert doctor.is_admin() is False
            assert doctor.is_patient() is False
            
            assert patient.is_patient() is True
            assert patient.is_admin() is False
            assert patient.is_doctor() is False
    
    def test_user_get_id(self, test_app):
        """Test user ID retrieval."""
        with test_app.app_context():
            user = User(email='test@example.com', full_name='Test', role='patient')
            user.set_password('testpass123')  # Add password to satisfy NOT NULL constraint
            db.session.add(user)
            db.session.commit()
            
            assert user.get_id() == str(user.id)


class TestDepartmentModel:
    """Unit tests for Department model."""
    
    def test_department_creation(self, test_app):
        """Test creating a department."""
        with test_app.app_context():
            dept = Department(
                name='Neurology',
                description='Brain and nervous system',
                is_active=True
            )
            db.session.add(dept)
            db.session.commit()
            
            assert dept.id is not None
            assert dept.name == 'Neurology'
            assert dept.is_active is True
    
    def test_department_unique_name(self, test_app):
        """Test department name uniqueness."""
        with test_app.app_context():
            dept1 = Department(name='Cardiology', description='Heart')
            db.session.add(dept1)
            db.session.commit()
            
            dept2 = Department(name='Cardiology', description='Heart')
            db.session.add(dept2)
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()


class TestAppointmentModel:
    """Unit tests for Appointment model."""
    
    def test_appointment_creation(self, test_app, patient_user, doctor_user, department):
        """Test creating an appointment."""
        with test_app.app_context():
            appointment = Appointment(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                department_id=department.id,
                appointment_type='scheduled',
                appointment_date=datetime.utcnow() + timedelta(days=1),
                slot_time='10:00',
                status='scheduled',
                symptoms='Headache'
            )
            db.session.add(appointment)
            db.session.commit()
            
            assert appointment.id is not None
            assert appointment.patient_id == patient_user.id
            assert appointment.doctor_id == doctor_user.id
            assert appointment.status == 'scheduled'


class TestQueueEntryModel:
    """Unit tests for QueueEntry model."""
    
    def test_queue_entry_creation(self, test_app, patient_user, doctor_user):
        """Test creating a queue entry."""
        with test_app.app_context():
            queue_entry = QueueEntry(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                queue_position=1,
                status='waiting',
                priority=0
            )
            db.session.add(queue_entry)
            db.session.commit()
            
            assert queue_entry.id is not None
            assert queue_entry.patient_id == patient_user.id
            assert queue_entry.status == 'waiting'


class TestMedicalRecordModel:
    """Unit tests for MedicalRecord model."""
    
    def test_medical_record_creation(self, test_app, patient_user, doctor_user):
        """Test creating a medical record."""
        with test_app.app_context():
            record = MedicalRecord(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                symptoms='Fever and cough',
                diagnosis='Common cold',
                notes='Prescribed rest and fluids',
                vital_signs={'temperature': 98.6, 'bp': '120/80'}
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.id is not None
            assert record.patient_id == patient_user.id
            assert record.diagnosis == 'Common cold'


class TestPrescriptionModel:
    """Unit tests for Prescription model."""
    
    def test_prescription_creation(self, test_app, patient_user, doctor_user):
        """Test creating a prescription."""
        with test_app.app_context():
            record = MedicalRecord(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                symptoms='Headache',
                diagnosis='Migraine'
            )
            db.session.add(record)
            db.session.commit()
            
            prescription = Prescription(
                medical_record_id=record.id,
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                medications=[
                    {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Twice daily'}
                ],
                instructions='Take with food'
            )
            db.session.add(prescription)
            db.session.commit()
            
            assert prescription.id is not None
            assert len(prescription.medications) == 1


class TestDoctorAvailabilityModel:
    """Unit tests for DoctorAvailability model."""
    
    def test_doctor_availability_creation(self, test_app, doctor_user):
        """Test creating doctor availability."""
        with test_app.app_context():
            availability = DoctorAvailability(
                doctor_id=doctor_user.id,
                day_of_week=0,  # Monday
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                is_available=True
            )
            db.session.add(availability)
            db.session.commit()
            
            assert availability.id is not None
            assert availability.doctor_id == doctor_user.id
            assert availability.is_available is True

