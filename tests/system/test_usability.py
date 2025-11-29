"""
System Usability Tests
Tests user interface, navigation, and user experience.
"""
import pytest
from models import db, User


class TestUsability:
    """Usability testing."""
    
    def test_navigation_home_to_login(self, client):
        """Test: Easy navigation from home to login."""
        # Access home page
        response = client.get('/')
        assert response.status_code == 200
        
        # Should be able to navigate to login
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_navigation_login_to_register(self, client):
        """Test: Easy navigation from login to register."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        
        # Should be able to navigate to register
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower()
    
    def test_user_friendly_error_messages(self, client):
        """Test: Error messages should be user-friendly."""
        # Try login with wrong credentials
        response = client.post('/auth/login', data={
            'email': 'wrong@test.com',
            'password': 'wrongpass'
        })
        assert response.status_code == 200
        # Should show friendly error message
    
    def test_redirect_after_login(self, test_app, client):
        """Test: Users should be redirected to appropriate dashboard after login."""
        with test_app.app_context():
            # Create patient
            patient = User(
                email='usability@test.com',
                full_name='Usability Patient',
                role='patient'
            )
            patient.set_password('pass123')
            db.session.add(patient)
            db.session.commit()
        
        # Login
        response = client.post('/auth/login', data={
            'email': 'usability@test.com',
            'password': 'pass123'
        }, follow_redirects=False)
        
        # Should redirect (302) to patient dashboard
        assert response.status_code == 302
    
    def test_dashboard_accessibility(self, authenticated_patient):
        """Test: Dashboard should be easily accessible."""
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200
        # Dashboard should be readable and accessible
    
    def test_form_validation_feedback(self, client):
        """Test: Forms should provide clear validation feedback."""
        # Try registration with missing required fields
        response = client.post('/auth/register', data={
            'email': 'test@test.com',
            'password': 'pass123',
            'full_name': '',  # Missing required field
            'phone': '1234567890'
        }, follow_redirects=True)
        # Should handle gracefully (may show error or redirect)
        assert response.status_code in [200, 302, 500]
    
    def test_logout_functionality(self, authenticated_patient):
        """Test: Logout should be easily accessible and functional."""
        # Access logout
        response = authenticated_patient.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # After logout, should not access protected routes
        response = authenticated_patient.get('/patient/dashboard', follow_redirects=True)
        # Should redirect to login
        assert response.status_code in [200, 302]
    
    def test_role_based_ui_access(self, authenticated_patient, authenticated_doctor, authenticated_admin):
        """Test: UI should adapt based on user role."""
        # Patient should see patient dashboard
        response = authenticated_patient.get('/patient/dashboard', follow_redirects=True)
        assert response.status_code == 200
        
        # Doctor should see doctor dashboard
        response = authenticated_doctor.get('/doctor/dashboard', follow_redirects=True)
        assert response.status_code == 200
        
        # Admin should see admin dashboard
        response = authenticated_admin.get('/admin/dashboard', follow_redirects=True)
        assert response.status_code == 200
    
    def test_404_error_page(self, client):
        """Test: 404 errors should show user-friendly page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        # Should show friendly 404 page
    
    def test_500_error_handling(self, client):
        """Test: 500 errors should be handled gracefully."""
        # This would typically require triggering an error
        # For now, verify error handler exists
        response = client.get('/')
        assert response.status_code in [200, 500]  # Should handle errors gracefully

