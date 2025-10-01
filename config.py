import os

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-for-replit')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///mediqueue.db')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True
    }
    WTF_CSRF_ENABLED = True
