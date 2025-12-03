import unittest
from app import app, db
from models import User, Appointment, Department
from datetime import datetime, timedelta
from flask_login import login_user

class TestPatientDashboard(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test data
        self.department = Department(name="Cardiology", description="Heart stuff")
        db.session.add(self.department)
        
        self.doctor = User(username="doctor", email="doc@test.com", role="doctor", full_name="Dr. House")
        self.doctor.set_password("password")
        self.doctor.department = self.department
        db.session.add(self.doctor)
        
        self.patient = User(username="patient", email="pat@test.com", role="patient", full_name="John Doe")
        self.patient.set_password("password")
        db.session.add(self.patient)
        
        db.session.commit()

        # Create an appointment
        self.appointment = Appointment(
            patient_id=self.patient.id,
            doctor_id=self.doctor.id,
            department_id=self.department.id,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            slot_time="10:00",
            status="scheduled",
            symptoms="Headache"
        )
        db.session.add(self.appointment)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_dashboard_appointments_display(self):
        # Login as patient
        with self.client:
            self.client.post('/auth/login', data={
                'email': 'pat@test.com',
                'password': 'password'
            }, follow_redirects=True)
            
            response = self.client.get('/patient/dashboard')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            
            # Check for the new section header
            self.assertIn("Upcoming Appointments", html)
            
            # Check for the appointment details
            self.assertIn("Dr. House", html)
            self.assertIn("Cardiology", html)
            self.assertIn("10:00", html)

if __name__ == '__main__':
    unittest.main()
