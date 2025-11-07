from flask import Flask
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Check admin accounts
    admins = User.query.filter_by(role='admin').all()
    print("\nAdmin accounts in database:")
    print("=" * 50)
    if admins:
        for admin in admins:
            print(f"Email: {admin.email}")
            print(f"Name: {admin.full_name}")
            print(f"Active: {admin.is_active}")
            print("-" * 30)
    else:
        print("No admin accounts found.")
        print("\nYou can create an admin by:")
        print("1. Visit /setup in browser")
        print("2. Set ADMIN_EMAIL and ADMIN_PASSWORD env vars")
        print("-" * 30)
    
    # Check total users by role
    print("\nUser counts by role:")
    print("=" * 50)
    for role in ['admin', 'doctor', 'patient']:
        count = User.query.filter_by(role=role).count()
        print(f"{role.title()}: {count}")