import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///mediqueue.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
    USE_REDIS = os.environ.get('USE_REDIS', 'True').lower() == 'true'
    
    # Template settings
    TEMPLATE_AUTO_RELOAD = True
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Debug settings
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    PROPAGATE_EXCEPTIONS = True
    
    # SESSION_COOKIE_SECURE = False
    # SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
