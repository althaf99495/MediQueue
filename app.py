import eventlet
eventlet.monkey_patch()
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from config import Config
from models import db, User

from extensions import socketio, api, csrf

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)
app.config.from_object(Config)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.DEBUG)

# Initialize extensions
db.init_app(app)
socketio.init_app(app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    async_handlers=True
)
api.init_app(app)
csrf.init_app(app)

# Debug route to list all registered routes
@app.route('/debug/routes')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():
        output.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'path': str(rule)
        })
    return {'routes': output}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Import and register blueprints
from routes.auth import auth_bp
from routes.doctor import doctor_bp
from routes.patient import patient_bp
from routes.admin import admin_bp
from routes.setup import setup_bp
# Import API routes (this will register the namespaces)
from routes import api as api_routes

# Register blueprints with explicit names
app.register_blueprint(auth_bp, name='auth')
app.register_blueprint(doctor_bp, url_prefix='/doctor', name='doctor')
app.register_blueprint(patient_bp, url_prefix='/patient', name='patient')
app.register_blueprint(admin_bp, url_prefix='/admin', name='admin')
app.register_blueprint(setup_bp, name='setup')

# Create a main blueprint for base routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page route"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_doctor():
            return redirect(url_for('doctor.dashboard'))
        elif current_user.is_patient():
            return redirect(url_for('patient.dashboard'))
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index template: {str(e)}")
        return render_template('500.html'), 500

# Register main blueprint last to avoid route conflicts
app.register_blueprint(main_bp)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

with app.app_context():
    db.create_all()
    
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_email and admin_password:
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                email=admin_email,
                full_name='System Administrator',
                role='admin',
                phone=''
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account created: {admin_email}")
        else:
            print(f"Admin account already exists: {admin_email}")
    else:
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count == 0:
            print("\n" + "="*60)
            print("NO ADMIN ACCOUNT FOUND!")
            print("Please create an admin account by visiting /setup")
            print("Or set ADMIN_EMAIL and ADMIN_PASSWORD environment variables")
            print("="*60 + "\n")

def find_available_port(start_port, max_attempts=5):
    """Try to find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    raise OSError(f"Could not find an available port in range {start_port}-{start_port + max_attempts - 1}")

def get_lan_ip():
    """Best-effort detection of LAN IP for display purposes only."""
    import socket
    lan_ip = '127.0.0.1'
    try:
        # This does not send data; it selects the appropriate outbound interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            lan_ip = s.getsockname()[0]
    except Exception:
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
    return lan_ip

if __name__ == '__main__':
    from waitress import serve
    
    # Get port from environment or use default
    preferred_port = int(os.environ.get('FLASK_PORT', 5000))
    
    try:
        # Try to find an available port
        port = find_available_port(preferred_port)
        
        print("\n" + "="*60)
        print("MediQueue Server Starting with Waitress")
        print("="*60)
        if port != preferred_port:
            print(f"\nWARNING: Preferred port {preferred_port} was in use!")
            print(f"Using alternative port: {port}")
        
        lan_ip = get_lan_ip()
        
        print("\nAccess the application at:")
        print(f"Main page:     http://localhost:{port}")
        print(f"Network:       http://{lan_ip}:{port}")
        print(f"Admin setup:   http://localhost:{port}/setup")
        print(f"Login page:    http://localhost:{port}/login")
        print("\nAPI Documentation:")
        print(f"Swagger UI:    http://localhost:{port}/api/docs")
        print("="*60 + "\n")
        
        # Use SocketIO to serve the Flask app (supports WebSockets)
        socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        print("\nERROR: Failed to start the server!")
        print(f"Details: {str(e)}")
        print("\nPossible solutions:")
        print("1. Set a different port using FLASK_PORT environment variable")
        print("2. Stop any other applications using the port")
        print("3. Ensure you have permissions to bind to the port")
        print("4. Wait a few moments and try again (port may be in TIME_WAIT state)")
        raise

