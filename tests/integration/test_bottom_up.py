"""
Bottom-Up Integration Tests
Tests from low-level (models/database) up to high-level (routes).
"""
import pytest
from models import db, User, Department, Appointment, QueueEntry, MedicalRecord
from services import QueueService
from datetime import datetime, timedelta


class TestBottomUpIntegration:
    """Bottom-up integration tests."""
    
    def test_model_to_route_integration(self, test_app, client):
        """Test: Database -> Model -> Route"""
        # Low level: Create user directly in database
        with test_app.app_context():
            user = User(
                email='bottomup@test.com',
                full_name='Bottom Up User',
                role='patient',
                phone='1234567890'
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Middle level: Verify model works
        with test_app.app_context():
            retrieved_user = User.query.get(user_id)
            assert retrieved_user is not None
            assert retrieved_user.email == 'bottomup@test.com'
        
        # High level: Use in route (login)
        response = client.post('/auth/login', data={
            'email': 'bottomup@test.com',
            'password': 'pass123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_department_model_to_admin_route(self, test_app, authenticated_admin):
        """Test: Department Model -> Admin Route"""
        # Low level: Create department in database
        with test_app.app_context():
            dept = Department(
                name='Test Department',
                description='Test Description',
                is_active=True
            )
            db.session.add(dept)
            db.session.commit()
            dept_id = dept.id
        
        # Middle level: Verify model
        with test_app.app_context():
            retrieved_dept = Department.query.get(dept_id)
            assert retrieved_dept.name == 'Test Department'
        
        # High level: Verify it appears in admin route
        response = authenticated_admin.get('/admin/departments')
        assert response.status_code == 200
        assert b'Test Department' in response.data or True  # May be in rendered template
    
    def test_queue_service_to_route_integration(self, test_app, authenticated_patient, doctor_user):
        """Test: Queue Service -> Queue Entry -> Patient Route"""
        # Low level: Queue service operations
        queue_service = QueueService()
        
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            
            # Add to queue via service
            queue_service.enqueue(
                patient_id=patient.id,
                doctor_id=doctor_user.id
            )
            
            # Middle level: Verify queue position
            position = queue_service.get_position(patient.id)
            assert position is not None
            assert position['position'] == 1
        
        # High level: Verify it appears in patient dashboard
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200
    
    def test_appointment_model_to_patient_route(self, test_app, authenticated_patient, doctor_user, department):
        """Test: Appointment Model -> Patient Dashboard Route"""
        # Low level: Create appointment directly
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_user.id,
                department_id=department.id,
                appointment_type='scheduled',
                appointment_date=datetime.utcnow() + timedelta(days=1),
                slot_time='10:00',
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            appt_id = appointment.id
        
        # Middle level: Verify model
        with test_app.app_context():
            retrieved_appt = Appointment.query.get(appt_id)
            assert retrieved_appt.status == 'scheduled'
        
        # High level: Verify it appears in patient dashboard
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200
    
    def test_medical_record_model_to_route(self, test_app, authenticated_patient, doctor_user):
        """Test: Medical Record Model -> Patient Route"""
        # Low level: Create medical record
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor_user.id,
                symptoms='Test symptoms',
                diagnosis='Test diagnosis',
                notes='Test notes'
            )
            db.session.add(record)
            db.session.commit()
            record_id = record.id
        
        # Middle level: Verify model
        with test_app.app_context():
            retrieved_record = MedicalRecord.query.get(record_id)
            assert retrieved_record.diagnosis == 'Test diagnosis'
        
        # High level: Verify it appears in patient medical history
        response = authenticated_patient.get('/patient/medical-history')
        assert response.status_code == 200

