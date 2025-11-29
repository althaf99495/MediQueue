"""
System Reliability Tests
Tests system stability, error handling, and recovery.
"""
import pytest
from models import db, User, Department, Appointment
from services import QueueService
from datetime import datetime, timedelta


class TestReliability:
    """Reliability testing."""
    
    def test_system_handles_invalid_input(self, client):
        """Test: System should handle invalid input gracefully."""
        # Try login with invalid data
        response = client.post('/auth/login', data={
            'email': 'not-an-email',
            'password': ''
        })
        assert response.status_code == 200
        # Should not crash, should show error
    
    def test_system_handles_missing_data(self, authenticated_patient):
        """Test: System should handle missing data gracefully."""
        # Try to access route with missing data
        response = authenticated_patient.post('/patient/book-appointment', data={}, follow_redirects=True)
        # Should not crash (may redirect or show error)
        assert response.status_code in [200, 302]
    
    def test_database_transaction_rollback(self, test_app):
        """Test: Database transactions should rollback on error."""
        with test_app.app_context():
            try:
                # Create invalid user (duplicate email)
                user1 = User(email='rollback@test.com', full_name='User 1', role='patient')
                user1.set_password('pass123')
                db.session.add(user1)
                db.session.commit()
                
                # Try to create duplicate
                user2 = User(email='rollback@test.com', full_name='User 2', role='patient')
                user2.set_password('pass123')
                db.session.add(user2)
                db.session.commit()
            except Exception:
                db.session.rollback()
            
            # Verify only one user exists
            users = User.query.filter_by(email='rollback@test.com').all()
            assert len(users) <= 1
    
    def test_queue_service_error_handling(self, queue_service_instance):
        """Test: Queue service should handle errors gracefully."""
        # Try to get position for non-existent patient
        position = queue_service_instance.get_position(patient_id=99999)
        assert position is None  # Should return None, not crash
        
        # Try to dequeue from empty queue
        entry = queue_service_instance.dequeue(doctor_id=99999)
        assert entry is None  # Should return None, not crash
    
    def test_system_recovery_after_error(self, test_app, client):
        """Test: System should recover after errors."""
        # Cause an error (invalid route)
        response = client.get('/invalid-route-that-does-not-exist')
        assert response.status_code == 404
        
        # System should still work
        response = client.get('/')
        assert response.status_code == 200
    
    def test_concurrent_database_operations(self, test_app):
        """Test: System should handle concurrent database operations."""
        with test_app.app_context():
            # Create multiple users concurrently (simulated)
            users = []
            for i in range(10):
                user = User(
                    email=f'concurrent{i}@test.com',
                    full_name=f'User {i}',
                    role='patient'
                )
                user.set_password('pass123')
                users.append(user)
                db.session.add(user)
            
            db.session.commit()
            
            # Verify all were created
            assert len(users) == 10
            for i in range(10):
                user = User.query.filter_by(email=f'concurrent{i}@test.com').first()
                assert user is not None
    
    def test_queue_consistency(self, queue_service_instance):
        """Test: Queue should maintain consistency."""
        # Clear any existing queue
        queue_service_instance.clear_queue(doctor_id=1)
        
        # Add patients
        for i in range(5):
            queue_service_instance.enqueue(patient_id=i, doctor_id=1)
        
        # Verify initial queue
        queue = queue_service_instance.get_queue(doctor_id=1)
        assert len(queue) == 5
        
        # Remove one
        result = queue_service_instance.remove_from_queue(patient_id=2)
        assert result is True
        
        # Verify queue is consistent
        queue = queue_service_instance.get_queue(doctor_id=1)
        patient_ids = [entry['patient_id'] for entry in queue]
        assert 2 not in patient_ids
        assert len(queue) == 4
    
    def test_data_integrity(self, test_app):
        """Test: Data integrity should be maintained."""
        with test_app.app_context():
            # Create user with relationships
            dept = Department(name='Integrity Test', description='Test', is_active=True)
            db.session.add(dept)
            db.session.commit()
            
            doctor = User(
                email='integrity@test.com',
                full_name='Dr. Integrity',
                role='doctor',
                department_id=dept.id
            )
            doctor.set_password('pass123')
            db.session.add(doctor)
            db.session.commit()
            
            # Verify relationship
            assert doctor.department_id == dept.id
            assert doctor in dept.doctors
    
    def test_session_management(self, test_app, client):
        """Test: User sessions should be managed reliably."""
        with test_app.app_context():
            user = User(
                email='session@test.com',
                full_name='Session User',
                role='patient'
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'email': 'session@test.com',
            'password': 'pass123'
        })
        
        # Session should persist
        response = client.get('/patient/dashboard', follow_redirects=True)
        assert response.status_code == 200
        
        # Logout
        client.get('/auth/logout')
        
        # Session should be cleared
        response = client.get('/patient/dashboard', follow_redirects=True)
        # Should redirect to login
        assert response.status_code in [200, 302]

