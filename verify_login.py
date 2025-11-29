import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re

# Base URL
BASE_URL = 'http://localhost:5000'

# Setup cookie jar to persist cookies (session)
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

def get_csrf_token(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.getcode() != 200:
                print(f"Failed to load {url}: {response.getcode()}")
                return None
            
            html = response.read().decode('utf-8')
            
            # Extract CSRF token using regex
            match = re.search(r'<input type="hidden" name="csrf_token" value="([^"]+)">', html)
            if match:
                return match.group(1)
            
            # Also check meta tag
            match = re.search(r'<meta name="csrf-token" content="([^"]+)">', html)
            if match:
                return match.group(1)
                
            print("Could not find CSRF token")
            return None
    except urllib.error.URLError as e:
        print(f"Error accessing {url}: {e}")
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
    # Using default admin credentials or a test user
    # Let's try to register a temporary user first to be sure
    print("   (Registering temp user for verification)")
    register_url = f"{BASE_URL}/auth/register"
    
    # We need to get CSRF from register page to be safe, though session cookie should handle it
    # But let's just use the one we have if it works, or fetch fresh.
    # Fetching fresh is safer.
    csrf_token_reg = get_csrf_token(register_url)
    
    register_data = urllib.parse.urlencode({
        'csrf_token': csrf_token_reg,
        'full_name': 'Verify User',
        'email': 'verify_urllib@test.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'patient',
        'phone': '5551234567',
        'age': '30',
        'gender': 'Other',
        'address': 'Test Address',
        'blood_group': 'O+'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(register_url, data=register_data)
        with urllib.request.urlopen(req) as reg_response:
            # If registration succeeds, it usually redirects to login or dashboard
            # urllib follows redirects automatically by default
            print(f"   Registration response URL: {reg_response.geturl()}")
            if "login" in reg_response.geturl() or "dashboard" in reg_response.geturl():
                 print("   Registration successful (redirected)")
            else:
                 print("   Registration completed (check if successful)")
    except urllib.error.HTTPError as e:
        print(f"   Registration failed: {e}")

    print("3. Logging in...")
    # Refresh CSRF from login page
    csrf_token = get_csrf_token(login_url)
    
    login_data = urllib.parse.urlencode({
        'csrf_token': csrf_token,
        'email': 'verify_urllib@test.com',
        'password': 'password123'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(login_url, data=login_data)
        with urllib.request.urlopen(req) as login_response:
            final_url = login_response.geturl()
            print(f"   Login final URL: {final_url}")
            
            if "dashboard" in final_url:
                print("   Accessed Dashboard successfully")
                return True
            elif "login" in final_url:
                # Check for error message in content
                content = login_response.read().decode('utf-8')
                if "Invalid email or password" in content:
                    print("   Login failed: Invalid credentials")
                else:
                    print("   Login failed: Remained on login page")
                return False
            else:
                print(f"   Login redirected to unexpected URL: {final_url}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"   Login request failed: {e}")
        return False

if __name__ == "__main__":
    try:
        if verify_login():
            print("\n✅ Login Verification PASSED")
        else:
            print("\n❌ Login Verification FAILED")
    except Exception as e:
        print(f"\n❌ Error: {e}")
