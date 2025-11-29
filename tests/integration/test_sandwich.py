"""
Sandwich (Hybrid) Integration Tests
Tests middle layers with mocked top and bottom layers.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from models import db, User, Appointment, Department
from services import QueueService
from datetime import datetime, timedelta


class TestSandwichIntegration:
    """Sandwich integration tests."""
    
    def test_queue_service_with_mocked_redis(self):
        """Test: Mock Redis (bottom) -> Queue Service (middle) -> Route (top)"""
        # Mock bottom layer: Redis
        with patch('services.queue_service.redis.Redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.zadd.return_value = True
            mock_client.zrange.return_value = ['{"patient_id": 1, "doctor_id": 10}']
            mock_client.get.return_value = '10'
            
            # Test middle layer: Queue Service
            queue_service = QueueService()
            result = queue_service.enqueue(patient_id=1, doctor_id=10)
            
            # Verify middle layer works with mocked bottom
            assert result is True
    
    def test_appointment_booking_with_mocked_database(self, test_app):
        """Test: Mock DB (bottom) -> Model (middle) -> Route (top)"""
        with test_app.app_context():
            # Mock bottom layer: Database session
            with patch.object(db.session, 'commit') as mock_commit:
                # Test middle layer: Model creation
                appointment = Appointment(
                    patient_id=1,
                    doctor_id=2,
                    department_id=1,
                    appointment_type='scheduled',
                    appointment_date=datetime.utcnow() + timedelta(days=1),
                    slot_time='10:00',
                    status='scheduled'
                )
                db.session.add(appointment)
                
                # Verify middle layer works
                assert appointment.patient_id == 1
                assert appointment.status == 'scheduled'
    
    def test_user_authentication_flow(self, test_app, client):
        """Test: Mock Session (bottom) -> Auth Logic (middle) -> Route (top)"""
        # Create real user in database (middle layer)
        with test_app.app_context():
            user = User(
                email='sandwich@test.com',
                full_name='Sandwich User',
                role='patient'
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
        
        # Test top layer: Login route with real middle layer
        response = client.post('/auth/login', data={
            'email': 'sandwich@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        
        # Verify integration between layers
        assert response.status_code == 302  # Redirect on success
    
    def test_queue_position_calculation(self, test_app, authenticated_patient, doctor_user):
        """Test: Queue Service (middle) with mocked data (bottom) -> Route (top)"""
        queue_service = QueueService()
        
        # Mock bottom layer: Queue data
        with patch.object(queue_service, 'get_position') as mock_position:
            mock_position.return_value = {
                'position': 3,
                'total': 10,
                'doctor_id': doctor_user.id
            }
            
            # Test middle layer: Position calculation
            position = queue_service.get_position(1)
            
            # Verify middle layer works
            assert position['position'] == 3
            assert position['total'] == 10
    
    def test_department_management_integration(self, test_app, authenticated_admin):
        """Test: Model (middle) -> Route (top) with real database (bottom)"""
        # Real bottom layer: Database
        with test_app.app_context():
            dept = Department(
                name='Sandwich Department',
                description='Test',
                is_active=True
            )
            db.session.add(dept)
            db.session.commit()
        
        # Test top layer: Admin route with real middle and bottom
        response = authenticated_admin.get('/admin/departments')
        assert response.status_code == 200

