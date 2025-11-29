from app import app, db
from models import Department

def add_departments():
    departments = [
        {"name": "General Medicine", "description": "Primary care and general health services"},
        {"name": "Cardiology", "description": "Heart and cardiovascular system care"},
        {"name": "Pediatrics", "description": "Medical care for infants, children, and adolescents"},
        {"name": "Orthopedics", "description": "Musculoskeletal system care"},
        {"name": "Neurology", "description": "Nervous system disorders and treatment"}
    ]

    with app.app_context():
        print("Adding departments...")
        for dept_data in departments:
            existing = Department.query.filter_by(name=dept_data["name"]).first()
            if not existing:
                dept = Department(
                    name=dept_data["name"],
                    description=dept_data["description"],
                    is_active=True
                )
                db.session.add(dept)
                print(f"Added: {dept_data['name']}")
            else:
                print(f"Skipped (already exists): {dept_data['name']}")
        
        try:
            db.session.commit()
            print("Departments added successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding departments: {e}")

if __name__ == "__main__":
    add_departments()
