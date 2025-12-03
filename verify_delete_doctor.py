import unittest
from app import app, db
from models import User, Department
from flask_login import login_user

class TestDeleteDoctor(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create admin
        self.admin = User(email="admin@test.com", role="admin", full_name="Admin User")
        self.admin.set_password("password")
        db.session.add(self.admin)

        # Create doctor to delete
        self.doctor = User(email="doc@test.com", role="doctor", full_name="Dr. Delete Me")
        self.doctor.set_password("password")
        db.session.add(self.doctor)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_delete_doctor(self):
        # Login as admin
        with self.client:
            self.client.post('/auth/login', data={
                'email': 'admin@test.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # Try to delete the doctor
            response = self.client.post(f'/admin/doctors/{self.doctor.id}/delete', 
                                      data={'hard_delete': 'true'},
                                      headers={'X-Requested-With': 'XMLHttpRequest'})
            
            print(f"Status Code: {response.status_code}")
            if response.is_json:
                print(f"Response Data: {response.get_json()}")
            else:
                print(f"Response Text: {response.get_data(as_text=True)}")

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.is_json)
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['action'], 'deleted')
            
            # Verify doctor is gone
            doctor = User.query.get(self.doctor.id)
            self.assertIsNone(doctor)

if __name__ == '__main__':
    import sys
    with open('test_result.txt', 'w') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        unittest.main(testRunner=runner, exit=False)
