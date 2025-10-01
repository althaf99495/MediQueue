import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from extensions import db, login_manager
from config import Config
from datetime import datetime

logging.basicConfig(level=logging.INFO)
migrate = Migrate()

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
        
    with app.app_context():
        from routes import (auth_bp, admin_bp, receptionist_bp, doctor_bp, public_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(receptionist_bp, url_prefix='/receptionist')
        app.register_blueprint(doctor_bp, url_prefix='/doctor')
        app.register_blueprint(public_bp)

    @app.errorhandler(404)
    def handle_not_found(e):
        return "Page not found.", 404
    
    @app.errorhandler(500)
    def handle_server_error(e):
        logging.error(f"Server error: {e}", exc_info=True)
        return "An internal server error occurred.", 500

    return app