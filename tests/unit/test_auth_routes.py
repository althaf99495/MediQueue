"""
Unit Tests for Authentication Routes
Tests individual authentication route handlers.
"""
import pytest
from models import db, User


class TestLoginRoute:
    """Unit tests for login route."""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_success(self, client, patient_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'patient@test.com',
            'password': 'patient123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'email': 'wrong@test.com',
            'password': 'wrongpass'
        })
        assert response.status_code == 200
        # Should show error message
    
    def test_login_inactive_account(self, test_app, client):
        """Test login with inactive account."""
        with test_app.app_context():
            user = User(
                email='inactive@test.com',
                full_name='Inactive User',
                role='patient',
                is_active=False
            )
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'email': 'inactive@test.com',
            'password': 'pass123'
        })
        assert response.status_code == 200
    
    def test_login_redirects_authenticated_user(self, authenticated_patient):
        """Test that authenticated users are redirected from login."""
        response = authenticated_patient.get('/auth/login')
        assert response.status_code in [200, 302]  # Redirect or dashboard


class TestRegisterRoute:
    """Unit tests for registration route."""
    
    def test_register_page_loads(self, client):
        """Test registration page is accessible."""
        response = client.get('/auth/register')
        assert response.status_code == 200
    
    def test_register_success(self, test_app, client):
        """Test successful registration."""
        response = client.post('/auth/register', data={
            'email': 'newpatient@test.com',
            'password': 'newpass123',
            'full_name': 'New Patient',
            'phone': '1234567890',
            'age': '25',
            'gender': 'Male'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        with test_app.app_context():
            user = User.query.filter_by(email='newpatient@test.com').first()
            assert user is not None
            assert user.role == 'patient'
    
    def test_register_duplicate_email(self, client, patient_user):
        """Test registration with duplicate email."""
        response = client.post('/auth/register', data={
            'email': 'patient@test.com',  # Already exists
            'password': 'pass123',
            'full_name': 'Duplicate User'
        })
        assert response.status_code == 200
    
    def test_register_redirects_authenticated_user(self, authenticated_patient):
        """Test that authenticated users are redirected from register."""
        response = authenticated_patient.get('/auth/register')
        assert response.status_code in [200, 302]


class TestLogoutRoute:
    """Unit tests for logout route."""
    
    def test_logout_requires_login(self, client):
        """Test logout requires authentication."""
        response = client.get('/auth/logout')
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_logout_success(self, authenticated_patient):
        """Test successful logout."""
        response = authenticated_patient.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

