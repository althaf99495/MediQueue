# scripts/create_or_reset_admin.py
import os
import sys
import getpass
from pathlib import Path

# Ensure project root is on sys.path so imports work when running this script
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from app import app
    from models import db, User
except Exception as e:
    print(f"Failed to import application context: {e}")
    print("Make sure you run this script from the project root or that the project structure is intact.")
    raise

def main():
    # Prefer env vars if set, otherwise prompt
    email = os.environ.get('ADMIN_EMAIL') or input("Admin email to create/reset: ").strip()
    if not email:
        print("Email required.")
        return

    pwd = os.environ.get('ADMIN_PASSWORD')
    if not pwd:
        pwd = getpass.getpass("New admin password (input hidden): ").strip()
    if not pwd:
        print("Password required.")
        return

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(pwd)
            user.role = 'admin'
            user.is_active = True
            print(f"Updated password for existing user: {email}")
        else:
            user = User(email=email, full_name='System Administrator', role='admin', phone='')
            user.set_password(pwd)
            db.session.add(user)
            print(f"Created new admin: {email}")
        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    main()