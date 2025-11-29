import requests
import re

# Base URL
BASE_URL = 'http://localhost:5000'

# Create a session to persist cookies
session = requests.Session()

def get_csrf_token(url):
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to load {url}: {response.status_code}")
        return None
    
    # Extract CSRF token using regex
    match = re.search(r'<input type="hidden" name="csrf_token" value="([^"]+)">', response.text)
    if match:
        return match.group(1)
    
    # Also check meta tag
    match = re.search(r'<meta name="csrf-token" content="([^"]+)">', response.text)
    if match:
        return match.group(1)
        
    print("Could not find CSRF token")
    return None

def verify_login():
    print("1. Getting CSRF token from login page...")
    login_url = f"{BASE_URL}/auth/login"
    csrf_token = get_csrf_token(login_url)
    
    if not csrf_token:
        print("Failed to get CSRF token")
        return False
        
    print(f"   CSRF Token: {csrf_token[:10]}...")
    
    print("2. Attempting login as admin...")
    # Assuming admin user exists from previous setup or tests
    # If not, we might need to create one or use the one created in tests if DB persisted
    # Let's try the default admin credentials if they exist, or the ones from verify_db.py if applicable
    # Actually, verify_db.py didn't create users.
    # But I can check if any user exists or register one.
    
    # Let's try to register a temporary user first to be sure
    print("   (Registering temp user for verification)")
    register_url = f"{BASE_URL}/auth/register"
    register_data = {
        'csrf_token': csrf_token,
        'full_name': 'Verify User',
        'email': 'verify@test.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'patient',
        'phone': '5551234567',
        'age': '30',
        'gender': 'Other',
        'address': 'Test Address',
        'blood_group': 'O+'
    }
    
    # We need a fresh CSRF for register page potentially? 
    # Usually the token is per session, but let's just use the one we got.
    # Better to get it from register page.
    csrf_token_reg = get_csrf_token(register_url)
    register_data['csrf_token'] = csrf_token_reg
    
    reg_response = session.post(register_url, data=register_data)
    
    # If registration succeeds, it usually redirects to login or dashboard
    if reg_response.status_code == 200 and "Registration successful" in reg_response.text:
        print("   Registration successful (or at least page loaded with success message)")
    elif reg_response.status_code == 302:
        print("   Registration redirected (likely success)")
    else:
        # It might fail if user already exists, which is fine, we proceed to login
        print(f"   Registration response: {reg_response.status_code}")

    print("3. Logging in...")
    login_data = {
        'csrf_token': csrf_token, # Use the one from login page
        'email': 'verify@test.com',
        'password': 'password123'
    }
    
    # Refresh CSRF from login page just in case
    login_data['csrf_token'] = get_csrf_token(login_url)
    
    login_response = session.post(login_url, data=login_data)
    
    if login_response.status_code == 200 and "Invalid email or password" in login_response.text:
        print("   Login failed: Invalid credentials")
        return False
    elif login_response.status_code == 302:
        print("   Login redirected (Success!)")
        # Follow redirect
        dashboard_response = session.get(f"{BASE_URL}/patient/dashboard")
        if dashboard_response.status_code == 200:
            print("   Accessed Patient Dashboard successfully")
            return True
        else:
            print(f"   Failed to access dashboard: {dashboard_response.status_code}")
            return False
    else:
        print(f"   Login response: {login_response.status_code}")
        # Check if we are on dashboard
        if "Dashboard" in login_response.text:
             print("   Login successful (landed on dashboard)")
             return True
        return False

if __name__ == "__main__":
    try:
        if verify_login():
            print("\n✅ Login Verification PASSED")
        else:
            print("\n❌ Login Verification FAILED")
    except Exception as e:
        print(f"\n❌ Error: {e}")
