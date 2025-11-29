"""
Unit Tests for Admin Routes
Tests individual admin route handlers.
"""
import pytest


class TestAdminDashboard:
    """Unit tests for admin dashboard."""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/admin/dashboard')
        assert response.status_code in [302, 401]
    
    def test_dashboard_requires_admin_role(self, authenticated_patient):
        """Test dashboard requires admin role."""
        response = authenticated_patient.get('/admin/dashboard')
        assert response.status_code in [302, 403]
    
    def test_dashboard_loads(self, authenticated_admin):
        """Test admin dashboard loads successfully."""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200


class TestAdminDepartments:
    """Unit tests for department management."""
    
    def test_departments_page_loads(self, authenticated_admin):
        """Test departments page loads."""
        response = authenticated_admin.get('/admin/departments')
        assert response.status_code == 200
    
    def test_create_department(self, authenticated_admin):
        """Test creating a department."""
        response = authenticated_admin.post('/admin/departments/add', data={
            'name': 'Test Department',
            'description': 'Test Description'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestAdminDoctors:
    """Unit tests for doctor management."""
    
    def test_doctors_page_loads(self, authenticated_admin):
        """Test doctors page loads."""
        response = authenticated_admin.get('/admin/doctors')
        assert response.status_code == 200


class TestAdminPatients:
    """Unit tests for patient management."""
    
    def test_patients_page_loads(self, authenticated_admin):
        """Test patients page loads."""
        response = authenticated_admin.get('/admin/patients')
        assert response.status_code == 200

