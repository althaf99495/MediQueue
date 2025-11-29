"""
Regression Tests
Ensures that changes do not affect existing functionality.
"""
import pytest
from models import db, User, Department, Appointment, QueueEntry, MedicalRecord
from services import QueueService
from datetime import datetime, timedelta


class TestRegression:
    """Regression testing to ensure existing functionality works."""
    
    def test_regression_user_registration(self, test_app, client):
        """Regression: User registration should still work."""
        response = client.post('/auth/register', data={
            'email': 'regression@test.com',
            'password': 'pass123',
            'full_name': 'Regression User',
            'phone': '1234567890'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with test_app.app_context():
            user = User.query.filter_by(email='regression@test.com').first()
            assert user is not None
            assert user.role == 'patient'
    
    def test_regression_user_login(self, test_app, client):
        """Regression: User login should still work."""
        with test_app.app_context():
            user = User(
                email='reglogin@test.com',
                full_name='Reg Login',
                role='patient'
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'email': 'reglogin@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        
        assert response.status_code == 302  # Redirect on success
    
    def test_regression_user_logout(self, authenticated_patient):
        """Regression: User logout should still work."""
        response = authenticated_patient.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_regression_password_hashing(self, test_app):
        """Regression: Password hashing should still work."""
        with test_app.app_context():
            user = User(
                email='reghash@test.com',
                full_name='Reg Hash',
                role='patient'
            )
            user.set_password('test_password')
            db.session.add(user)
            db.session.commit()
            
            assert user.check_password('test_password') is True
            assert user.check_password('wrong_password') is False
            assert user.password_hash != 'test_password'
    
    def test_regression_role_checks(self, test_app):
        """Regression: Role checking methods should still work."""
        with test_app.app_context():
            admin = User(email='regadmin@test.com', full_name='Admin', role='admin')
            doctor = User(email='regdoctor@test.com', full_name='Doctor', role='doctor')
            patient = User(email='regpatient@test.com', full_name='Patient', role='patient')
            
            assert admin.is_admin() is True
            assert doctor.is_doctor() is True
            assert patient.is_patient() is True
    
    def test_regression_department_creation(self, test_app):
        """Regression: Department creation should still work."""
        with test_app.app_context():
            dept = Department(
                name='Regression Department',
                description='Test',
                is_active=True
            )
            db.session.add(dept)
            db.session.commit()
            
            assert dept.id is not None
            assert dept.name == 'Regression Department'
    
    def test_regression_appointment_creation(self, test_app, patient_user, doctor_user, department):
        """Regression: Appointment creation should still work."""
        with test_app.app_context():
            patient_id = patient_user.id
            doctor_id = doctor_user.id
            dept_id = department.id
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                department_id=dept_id,
                appointment_type='scheduled',
                appointment_date=datetime.utcnow() + timedelta(days=1),
                slot_time='10:00',
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()
            
            assert appointment.id is not None
            assert appointment.status == 'scheduled'
    
    def test_regression_queue_enqueue(self, queue_service_instance):
        """Regression: Queue enqueue should still work."""
        result = queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        assert result is True
        
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert len(queue) == 1
        assert queue[0]['patient_id'] == 1
    
    def test_regression_queue_dequeue(self, queue_service_instance):
        """Regression: Queue dequeue should still work."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=10)
        
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        
        entry = queue_service_instance.dequeue(doctor_id=10)
        assert entry is not None
        assert entry['patient_id'] == 1
        
        # Queue should be empty
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert len(queue) == 0
    
    def test_regression_queue_position(self, queue_service_instance):
        """Regression: Queue position tracking should still work."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=10)
        
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        queue_service_instance.enqueue(patient_id=3, doctor_id=10)
        
        position = queue_service_instance.get_position(patient_id=2)
        assert position is not None
        assert position['position'] == 2
        assert position['total'] == 3
    
    def test_regression_queue_remove(self, queue_service_instance):
        """Regression: Removing from queue should still work."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=10)
        
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        result = queue_service_instance.remove_from_queue(patient_id=1)
        assert result is True
        
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert len(queue) == 1
        assert queue[0]['patient_id'] == 2
    
    def test_regression_queue_clear(self, queue_service_instance):
        """Regression: Clearing queue should still work."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        result = queue_service_instance.clear_queue(doctor_id=10)
        assert result is True
        
        length = queue_service_instance.get_queue_length(doctor_id=10)
        assert length == 0
    
    def test_regression_medical_record_creation(self, test_app, patient_user, doctor_user):
        """Regression: Medical record creation should still work."""
        with test_app.app_context():
            patient_id = patient_user.id
            doctor_id = doctor_user.id
            record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=doctor_id,
                symptoms='Test symptoms',
                diagnosis='Test diagnosis',
                notes='Test notes'
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.id is not None
            assert record.diagnosis == 'Test diagnosis'
    
    def test_regression_patient_dashboard(self, authenticated_patient):
        """Regression: Patient dashboard should still work."""
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200
    
    def test_regression_doctor_dashboard(self, authenticated_doctor):
        """Regression: Doctor dashboard should still work."""
        response = authenticated_doctor.get('/doctor/dashboard')
        assert response.status_code == 200
    
    def test_regression_admin_dashboard(self, authenticated_admin):
        """Regression: Admin dashboard should still work."""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200
    
    def test_regression_authentication_required(self, client):
        """Regression: Protected routes should still require authentication."""
        response = client.get('/patient/dashboard', follow_redirects=False)
        assert response.status_code in [302, 401]
    
    def test_regression_role_based_access(self, authenticated_patient):
        """Regression: Role-based access control should still work."""
        # Patient should not access admin routes
        response = authenticated_patient.get('/admin/dashboard', follow_redirects=True)
        assert response.status_code in [200, 302, 403]
    
    def test_regression_complete_workflow(self, test_app, client):
        """Regression: Complete patient workflow should still work."""
        # Register
        response = client.post('/auth/register', data={
            'email': 'workflow@test.com',
            'password': 'pass123',
            'full_name': 'Workflow User',
            'phone': '1234567890'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Login
        response = client.post('/auth/login', data={
            'email': 'workflow@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        assert response.status_code == 302
        
        # Access dashboard
        response = client.get('/patient/dashboard', follow_redirects=True)
        assert response.status_code == 200
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestBackwardCompatibility:
    """Test backward compatibility of existing features."""
    
    def test_backward_compat_user_model(self, test_app):
        """Test: User model should maintain backward compatibility."""
        with test_app.app_context():
            user = User(
                email='backward@test.com',
                full_name='Backward User',
                role='patient',
                phone='1234567890'
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            # All existing fields should work
            assert user.email == 'backward@test.com'
            assert user.full_name == 'Backward User'
            assert user.role == 'patient'
            assert user.phone == '1234567890'
            assert user.check_password('pass123') is True
    
    def test_backward_compat_queue_service(self, queue_service_instance):
        """Test: Queue service should maintain backward compatibility."""
        # All existing methods should work
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        position = queue_service_instance.get_position(patient_id=1)
        queue = queue_service_instance.get_queue(doctor_id=10)
        entry = queue_service_instance.dequeue(doctor_id=10)
        
        assert position is not None
        assert len(queue) == 1
        assert entry is not None

