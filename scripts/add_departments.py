# scripts/add_departments.py
import sys
from pathlib import Path

# Ensure project root on sys.path
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from models import db, Department

DEPARTMENTS = [
    {'name': 'General Medicine', 'description': 'Primary care and general practice.'},
    {'name': 'Cardiology', 'description': 'Heart and vascular care.'},
    {'name': 'Pediatrics', 'description': 'Child health and wellness.'},
    {'name': 'Orthopedics', 'description': 'Bone, joint and muscle care.'},
    {'name': 'Dermatology', 'description': 'Skin health and treatment.'},
]

def main():
    with app.app_context():
        for dept in DEPARTMENTS:
            existing = Department.query.filter_by(name=dept['name']).first()
            if existing:
                print(f"Skipping existing department: {existing.name}")
                continue
            d = Department(name=dept['name'], description=dept['description'])
            db.session.add(d)
            print(f"Added department: {dept['name']}")
        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    main()
