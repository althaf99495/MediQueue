import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['WTF_CSRF_ENABLED'] = 'False'

from app import app, db
from models import User, Department
from werkzeug.security import generate_password_hash

def reproduce():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False
    )
    
    with app.app_context():
        db.create_all()
        
        print("Creating department...")
        dept = Department(name='Beta Department', description='Test', is_active=True)
        db.session.add(dept)
        db.session.commit()
        
        print("Creating doctor...")
        doctor = User(
            email='betadoctor@test.com',
            full_name='Dr. Beta',
            role='doctor',
            department_id=dept.id,
            specialization='General',
            avg_consultation_time=15
        )
        print(f"Doctor created. Password hash before set: {doctor.password_hash}")
        doctor.set_password('pass123')
        print(f"Password hash after set: {doctor.password_hash}")
        
        db.session.add(doctor)
        try:
            db.session.commit()
            print("Doctor committed successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Caught exception: {e}")

if __name__ == "__main__":
    reproduce()
