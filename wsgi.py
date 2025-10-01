"""
WSGI entry point for the MediQueue application.

This script creates the Flask app instance and serves it using the Waitress WSGI server.
"""

from app import create_app
from waitress import serve

# Create the Flask app instance
app = create_app()

if __name__ == '__main__':
    print("--- MediQueue Server Starting ---")
    print("Access locally at: http://127.0.0.1:8000")
    serve(app, host='0.0.0.0', port=8000)
