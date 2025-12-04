"""
Pytest configuration and shared fixtures for all test types.
"""
import pytest
import os
from app import app, db
from models import User, Department, Appointment, QueueEntry, MedicalRecord, Prescription, DoctorAvailability
from services import QueueService
from datetime import datetime, timedelta


@pytest.fixture(scope='function')
def test_app():
    """Create and configure a test Flask application."""
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key-for-testing-only',
        ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'pdf'},
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    with app.app_context():
        db.session.expire_on_commit = False
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Clear queue state
        QueueService().clear_all()
        yield app
        db.session.remove()
        db.drop_all()
        QueueService().clear_all()


@pytest.fixture(scope='function')
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()
@pytest.fixture(scope='function')
def runner(test_app):
    """Create a test CLI runner."""
    return test_app.test_cli_runner()


@pytest.fixture(scope='function')
def admin_user(test_app):
    """Create a test admin user."""
    admin = User(
        email='admin@test.com',
        full_name='Test Admin',
        role='admin',
        phone='1234567890',
        is_active=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    db.session.refresh(admin)  # Refresh to ensure it's attached
    return admin


@pytest.fixture(scope='function')
def doctor_user(test_app):
    """Create a test doctor user."""
    doctor = User(
        email='doctor@test.com',
        full_name='Dr. Test Doctor',
        role='doctor',
        phone='1234567891',
        specialization='General Medicine',
        consultation_fee=500.0,
        avg_consultation_time=15,
        is_active=True
    )
    doctor.set_password('doctor123')
    db.session.add(doctor)
    db.session.commit()
    db.session.refresh(doctor)
    return doctor


@pytest.fixture(scope='function')
def patient_user(test_app):
    """Create a test patient user."""
    patient = User(
        email='patient@test.com',
        full_name='Test Patient',
        role='patient',
        phone='1234567892',
        age=30,
        gender='Male',
        address='123 Test St',
        blood_group='O+',
        is_active=True
    )
    patient.set_password('patient123')
    db.session.add(patient)
    db.session.commit()
    db.session.refresh(patient)
    return patient


@pytest.fixture(scope='function')
def department(test_app):
    """Create a test department."""
    dept = Department(
        name='Cardiology',
        description='Heart and cardiovascular diseases',
        is_active=True
    )
    db.session.add(dept)
    db.session.commit()
    db.session.refresh(dept)
    return dept


@pytest.fixture(scope='function')
def queue_service_instance():
    """Create a QueueService instance for testing."""
    service = QueueService()
    service.clear_all()
    yield service
    service.clear_all()


@pytest.fixture(scope='function')
def authenticated_admin(client, admin_user):
    """Login as admin and return client."""
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'admin123'
    })
    return client


@pytest.fixture(scope='function')
def authenticated_doctor(client, doctor_user):
    """Login as doctor and return client."""
    response = client.post('/auth/login', data={
        'email': 'doctor@test.com',
        'password': 'doctor123'
    })
    assert response.status_code == 302
    return client


@pytest.fixture(scope='function')
def authenticated_patient(client, patient_user):
    """Login as patient and return client."""
    client.post('/auth/login', data={
        'email': 'patient@test.com',
        'password': 'patient123'
    })
    return client

