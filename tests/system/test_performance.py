"""
System Performance Tests
Tests system performance, load handling, and response times.
"""
import pytest
import time
from models import db, User, Department, Appointment
from services import QueueService
from datetime import datetime, timedelta


class TestPerformance:
    """Performance testing."""
    
    def test_response_time_index_page(self, client):
        """Test: Index page should load quickly."""
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should load in under 1 second
    
    def test_response_time_login_page(self, client):
        """Test: Login page should load quickly."""
        start_time = time.time()
        response = client.get('/auth/login')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0
    
    def test_database_query_performance(self, test_app):
        """Test: Database queries should be fast."""
        with test_app.app_context():
            # Create test data
            for i in range(100):
                user = User(
                    email=f'perf{i}@test.com',
                    full_name=f'User {i}',
                    role='patient'
                )
                user.set_password('pass123')
                db.session.add(user)
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            users = User.query.filter_by(role='patient').all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert len(users) >= 100
            assert query_time < 0.5  # Should query in under 0.5 seconds
    
    def test_queue_service_performance(self, queue_service_instance):
        """Test: Queue operations should be fast."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=1)
        
        # Test enqueue performance
        start_time = time.time()
        for i in range(100):
            queue_service_instance.enqueue(patient_id=i, doctor_id=1)
        end_time = time.time()
        
        enqueue_time = end_time - start_time
        assert enqueue_time < 1.0  # 100 enqueues in under 1 second
        
        # Test get_queue performance
        start_time = time.time()
        queue = queue_service_instance.get_queue(doctor_id=1)
        end_time = time.time()
        
        get_queue_time = end_time - start_time
        assert len(queue) == 100
        assert get_queue_time < 0.5  # Should retrieve in under 0.5 seconds
    
    def test_concurrent_user_registration(self, test_app, client):
        """Test: System should handle concurrent registrations."""
        start_time = time.time()
        
        # Simulate concurrent registrations
        responses = []
        for i in range(10):
            response = client.post('/auth/register', data={
                'email': f'concurrent{i}@test.com',
                'password': 'pass123',
                'full_name': f'Concurrent {i}',
                'phone': f'123456789{i}'
            }, follow_redirects=True)
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert total_time < 5.0  # 10 registrations in under 5 seconds
    
    def test_large_queue_handling(self, queue_service_instance):
        """Test: System should handle large queues efficiently."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=1)
        
        # Create large queue
        start_time = time.time()
        for i in range(1000):
            queue_service_instance.enqueue(patient_id=i, doctor_id=1)
        end_time = time.time()
        
        creation_time = end_time - start_time
        assert creation_time < 5.0  # 1000 enqueues in under 5 seconds
        
        # Test position lookup in large queue
        start_time = time.time()
        position = queue_service_instance.get_position(patient_id=500)
        end_time = time.time()
        
        lookup_time = end_time - start_time
        assert position is not None
        assert lookup_time < 1.0  # Position lookup in under 1 second
    
    def test_dashboard_load_performance(self, authenticated_patient):
        """Test: Dashboard should load quickly with data."""
        start_time = time.time()
        response = authenticated_patient.get('/patient/dashboard')
        end_time = time.time()
        
        load_time = end_time - start_time
        assert response.status_code == 200
        assert load_time < 2.0  # Dashboard should load in under 2 seconds


class TestLoadHandling:
    """Load and stress testing."""
    
    def test_multiple_appointments_creation(self, test_app, authenticated_patient, doctor_user, department):
        """Test: System should handle multiple appointment creations."""
        with test_app.app_context():
            patient = User.query.filter_by(role='patient').first()
            patient_id = patient.id
            doctor_id = doctor_user.id
            dept_id = department.id
            
            start_time = time.time()
            appointments = []
            for i in range(50):
                future_date = (datetime.utcnow() + timedelta(days=i+1)).strftime('%Y-%m-%d')
                appointment = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    department_id=dept_id,
                    appointment_type='scheduled',
                    appointment_date=datetime.strptime(f"{future_date} 10:00", '%Y-%m-%d %H:%M'),
                    slot_time='10:00',
                    status='scheduled'
                )
                appointments.append(appointment)
                db.session.add(appointment)
            
            db.session.commit()
            end_time = time.time()
            
            creation_time = end_time - start_time
            assert len(appointments) == 50
            assert creation_time < 3.0  # 50 appointments in under 3 seconds
    
    def test_queue_dequeue_performance(self, queue_service_instance):
        """Test: Dequeue operations should be fast."""
        # Clear queue first
        queue_service_instance.clear_queue(doctor_id=1)
        
        # Create queue
        for i in range(100):
            queue_service_instance.enqueue(patient_id=i, doctor_id=1)
        
        # Test dequeue performance
        start_time = time.time()
        dequeued = []
        for i in range(100):
            entry = queue_service_instance.dequeue(doctor_id=1)
            if entry:
                dequeued.append(entry)
        end_time = time.time()
        
        dequeue_time = end_time - start_time
        assert len(dequeued) == 100
        assert dequeue_time < 2.0  # 100 dequeues in under 2 seconds

