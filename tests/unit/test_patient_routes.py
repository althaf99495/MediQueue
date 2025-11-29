"""
Unit Tests for Patient Routes
Tests individual patient route handlers.
"""
import pytest
from models import db, User, Appointment, Department, DoctorAvailability
from datetime import datetime, timedelta


class TestPatientDashboard:
    """Unit tests for patient dashboard."""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/patient/dashboard')
        assert response.status_code in [302, 401]
    
    def test_dashboard_requires_patient_role(self, authenticated_doctor):
        """Test dashboard requires patient role."""
        response = authenticated_doctor.get('/patient/dashboard')
        assert response.status_code in [302, 403]
    
    def test_dashboard_loads(self, authenticated_patient):
        """Test patient dashboard loads successfully."""
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200


class TestBookAppointment:
    """Unit tests for appointment booking."""
    
    def test_book_appointment_page_loads(self, authenticated_patient):
        """Test appointment booking page loads."""
        response = authenticated_patient.get('/patient/book-appointment')
        assert response.status_code == 200
    
    def test_book_appointment_success(self, test_app, authenticated_patient, doctor_user, department):
        """Test successful appointment booking."""
        with test_app.app_context():
            # Set up doctor availability
            availability = DoctorAvailability(
                doctor_id=doctor_user.id,
                day_of_week=0,  # Monday
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                is_available=True
            )
            db.session.add(availability)
            db.session.commit()
        
        future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = authenticated_patient.post('/patient/book-appointment', data={
            'doctor_id': doctor_user.id,
            'appointment_date': future_date,
            'slot_time': '10:00',
            'symptoms': 'Headache'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify appointment was created
        with test_app.app_context():
            patient = User.query.filter_by(email='patient@test.com').first()
            appointment = Appointment.query.filter_by(
                patient_id=patient.id,
                doctor_id=doctor_user.id
            ).first()
            assert appointment is not None
    
    def test_book_appointment_past_date(self, authenticated_patient, doctor_user):
        """Test booking appointment in the past."""
        past_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = authenticated_patient.post('/patient/book-appointment', data={
            'doctor_id': doctor_user.id,
            'appointment_date': past_date,
            'slot_time': '10:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Cannot book an appointment in the past' in response.data
    
    def test_book_appointment_invalid_doctor(self, authenticated_patient):
        """Test booking with invalid doctor ID."""
        future_date = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = authenticated_patient.post('/patient/book-appointment', data={
            'doctor_id': 99999,  # Non-existent doctor
            'appointment_date': future_date,
            'slot_time': '10:00'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid doctor selected' in response.data

