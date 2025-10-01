from .auth import auth_bp
from .admin import admin_bp
from .doctor import doctor_bp
from .receptionist import receptionist_bp
from .public import public_bp

__all__ = [
    "auth_bp",
    "admin_bp",
    "doctor_bp",
    "receptionist_bp",
    "public_bp",
]