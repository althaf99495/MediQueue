import click
from flask.cli import with_appcontext
from extensions import db
from models import User, Doctor, Patient
from datetime import date

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables and default users."""
    db.create_all()

    # Check if admin user already exists
    if User.query.filter_by(username='admin').first():
        click.echo("Database already initialized with default users.")
        return

    click.echo("Creating default users...")

    # Create Admin user
    admin_user = User(
        username='admin',
        email='admin@mediqueue.com',
        first_name='System',
        last_name='Administrator',
        phone='+1-555-0001',
        role='admin',
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)

    # Create Doctor user
    doctor_user = User(
        username='doctor',
        email='doctor@mediqueue.com',
        first_name='John',
        last_name='Smith',
        phone='+1-555-0002',
        role='doctor',
        is_active=True
    )
    doctor_user.set_password('doctor123')
    db.session.add(doctor_user)

    # Create Receptionist user
    receptionist_user = User(
        username='receptionist',
        email='receptionist@mediqueue.com',
        first_name='Jane',
        last_name='Doe',
        phone='+1-555-0003',
        role='receptionist',
        is_active=True
    )
    receptionist_user.set_password('receptionist123')
    db.session.add(receptionist_user)

    # Commit users first to get their IDs
    db.session.commit()

    click.echo("Creating doctor profile...")

    # Create Doctor profile
    doctor_profile = Doctor(
        user_id=doctor_user.id,
        license_number='MD123456',
        specialization='General Medicine',
        qualification='MBBS, MD',
        experience_years=10,
        consultation_fee=75.0,
        availability_status='available'
    )
    db.session.add(doctor_profile)

    # Create sample patients for demonstration
    click.echo("Creating sample patients...")

    sample_patients = [
        {
            'patient_id': 'P000001',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'date_of_birth': date(1985, 6, 15),
            'gender': 'female',
            'phone': '+1-555-1001',
            'email': 'alice.johnson@email.com',
            'blood_type': 'A+',
            'address': '123 Main St, Anytown, ST 12345'
        },
        {
            'patient_id': 'P000002',
            'first_name': 'Bob',
            'last_name': 'Williams',
            'date_of_birth': date(1978, 11, 22),
            'gender': 'male',
            'phone': '+1-555-1002',
            'email': 'bob.williams@email.com',
            'blood_type': 'O-',
            'address': '456 Oak Ave, Anytown, ST 12345'
        },
        {
            'patient_id': 'P000003',
            'first_name': 'Carol',
            'last_name': 'Brown',
            'date_of_birth': date(1992, 3, 8),
            'gender': 'female',
            'phone': '+1-555-1003',
            'email': 'carol.brown@email.com',
            'blood_type': 'B+',
            'address': '789 Pine Rd, Anytown, ST 12345'
        }
    ]

    for patient_data in sample_patients:
        patient = Patient(**patient_data)
        db.session.add(patient)

    db.session.commit()

    click.echo("Database initialized successfully!")
    click.echo("\n" + "="*50)
    click.echo("DEFAULT LOGIN CREDENTIALS:")
    click.echo("="*50)
    click.echo("Admin:")
    click.echo("  Username: admin")
    click.echo("  Password: admin123")
    click.echo("\nDoctor:")
    click.echo("  Username: doctor")
    click.echo("  Password: doctor123")
    click.echo("\nReceptionist:")
    click.echo("  Username: receptionist")
    click.echo("  Password: receptionist123")
    click.echo("="*50)

def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.cli.add_command(init_db_command)
