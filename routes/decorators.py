from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def role_required(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role."""
    return role_required('admin')(f)

def doctor_required(f):
    """Decorator to require doctor role."""
    return role_required('doctor')(f)

def receptionist_required(f):
    """Decorator to require receptionist role."""
    return role_required('receptionist')(f)

def admin_or_receptionist_required(f):
    """Decorator to require admin or receptionist role."""
    return role_required('admin', 'receptionist')(f)