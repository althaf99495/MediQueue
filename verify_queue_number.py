import unittest
from app import app, db
from models import User, QueueEntry
from services import QueueService
from flask_login import login_user
import datetime

class TestQueueNumber(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Reset QueueService
        self.queue_service = QueueService()
        self.queue_service.clear_all()

        # Create doctor
        self.doctor = User(email="doc@test.com", role="doctor", full_name="Dr. Queue")
        self.doctor.set_password("password")
        db.session.add(self.doctor)
        
        # Create patient
        self.patient = User(email="patient@test.com", role="patient", full_name="Patient Zero")
        self.patient.set_password("password")
        db.session.add(self.patient)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_queue_number_generation(self):
        # Login as patient
        with self.client:
            self.client.post('/auth/login', data={
                'email': 'patient@test.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # Join queue
            response = self.client.get(f'/patient/join-queue/{self.doctor.id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify DB entry
            entry = QueueEntry.query.filter_by(patient_id=self.patient.id).first()
            self.assertIsNotNone(entry)
            print(f"DB Queue Number: {entry.queue_number}")
            self.assertIsNotNone(entry.queue_number)
            self.assertEqual(entry.queue_number, 1)
            
            # Verify QueueService entry
            position = self.queue_service.get_position(self.patient.id)
            self.assertIsNotNone(position)
            print(f"Service Entry: {position['entry']}")
            self.assertIn('queue_number', position['entry'])
            self.assertEqual(position['entry']['queue_number'], 1)
            
            # Verify Dashboard Render
            response = self.client.get('/patient/dashboard')
            html = response.get_data(as_text=True)
            
            # Check for token number in HTML
            if f'#{entry.queue_number}' in html:
                print("Token number found in HTML")
            else:
                print("Token number NOT found in HTML")
                print("Snippet around queue-number:")
                try:
                    start = html.index('id="queue-number">')
                    print(html[start:start+100])
                except ValueError:
                    print("id='queue-number' not found")

if __name__ == '__main__':
    unittest.main()
