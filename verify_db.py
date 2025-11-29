from app import app, db
from models import User

with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    try:
        db.create_all()
        print("Tables created successfully.")
        
        # Verify User table exists
        users = User.query.all()
        print(f"User count: {len(users)}")
    except Exception as e:
        print(f"Error creating tables: {e}")
