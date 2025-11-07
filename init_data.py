from app import app, db
from models import User, Department

with app.app_context():
    departments_data = [
        {'name': 'Cardiology', 'description': 'Heart and cardiovascular system care'},
        {'name': 'Neurology', 'description': 'Brain and nervous system disorders'},
        {'name': 'Orthopedics', 'description': 'Bone, joint, and muscle treatment'},
        {'name': 'Pediatrics', 'description': 'Child healthcare and development'},
        {'name': 'General Medicine', 'description': 'General health and wellness'},
    ]
    
    for dept_data in departments_data:
        existing = Department.query.filter_by(name=dept_data['name']).first()
        if not existing:
            dept = Department(**dept_data)
            db.session.add(dept)
    
    cardiology = Department.query.filter_by(name='Cardiology').first()
    if cardiology:
        existing_doctor = User.query.filter_by(email='doctor@mediqueue.com').first()
        if not existing_doctor:
            doctor = User(
                email='doctor@mediqueue.com',
                full_name='Sarah Johnson',
                role='doctor',
                phone='9876543210',
                department_id=cardiology.id,
                specialization='Cardiologist',
                consultation_fee=150.0,
                avg_consultation_time=20
            )
            doctor.set_password('doctor123')
            db.session.add(doctor)
    
    db.session.commit()
    print("Sample data initialized successfully!")
    print("Doctor account: doctor@mediqueue.com / doctor123")
