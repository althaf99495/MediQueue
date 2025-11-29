"""
Unit Tests for Doctor Routes
Tests individual doctor route handlers.
"""
import pytest


class TestDoctorDashboard:
    """Unit tests for doctor dashboard."""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/doctor/dashboard')
        assert response.status_code in [302, 401]
    
    def test_dashboard_requires_doctor_role(self, authenticated_patient):
        """Test dashboard requires doctor role."""
        response = authenticated_patient.get('/doctor/dashboard')
        assert response.status_code in [302, 403]
    
    def test_dashboard_loads(self, authenticated_doctor):
        """Test doctor dashboard loads successfully."""
        response = authenticated_doctor.get('/doctor/dashboard')
        assert response.status_code == 200


class TestDoctorAvailability:
    """Unit tests for doctor availability management."""
    
    def test_availability_page_loads(self, authenticated_doctor):
        """Test availability page loads."""
        response = authenticated_doctor.get('/doctor/availability')
        assert response.status_code == 200
    
    def test_set_availability(self, authenticated_doctor):
        """Test setting doctor availability."""
        response = authenticated_doctor.post('/doctor/availability', data={
            'day_of_week': '0',
            'start_time': '09:00',
            'end_time': '17:00',
            'is_available': 'True'
        }, follow_redirects=True)
        assert response.status_code == 200

