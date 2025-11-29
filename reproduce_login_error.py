
import urllib.request
import urllib.parse
import urllib.error
import sys
import json

def reproduce_login_error(port=5000):
    base_url = f"http://localhost:{port}"
    print(f"Targeting {base_url}")
    
    # Cookie jar
    cookies = {}

    def make_request(url, data=None):
        req = urllib.request.Request(url, data=data)
        # Add cookies
        if cookies:
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            req.add_header('Cookie', cookie_header)
        
        try:
            with urllib.request.urlopen(req) as response:
                # Update cookies
                if 'Set-Cookie' in response.headers:
                    for cookie in response.headers.get_all('Set-Cookie'):
                        parts = cookie.split(';')[0].split('=')
                        if len(parts) == 2:
                            cookies[parts[0]] = parts[1]
                return response.status, response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8')
        except Exception as e:
            print(f"Request failed: {e}")
            return 0, str(e)

    # 1. Get CSRF Token
    print("Fetching CSRF token...")
    csrf_token = None
    try:
        status, body = make_request(f"{base_url}/auth/login")
        if "csrf_token" in body:
            # Simple extraction for demonstration
            import re
            match = re.search(r'name="csrf_token" value="([^"]+)"', body)
            if match:
                csrf_token = match.group(1)
                print(f"CSRF Token found: {csrf_token}")
            else:
                print("CSRF token not found in HTML")
        else:
            print("CSRF token input not found in response")
    except Exception as e:
        print(f"Failed to fetch CSRF token: {e}")

    if not csrf_token:
        print("Cannot proceed without CSRF token")
        return

    # 2. Register
    print("Registering...")
    register_data = urllib.parse.urlencode({
        'csrf_token': csrf_token,
        'email': 'debug_login@example.com',
        'password': 'password123',
        'full_name': 'Debug User',
        'phone': '1234567890',
        'role': 'patient',
        'age': '30',
        'gender': 'Male',
        'address': 'Test Address',
        'blood_group': 'O+',
        'emergency_contact': '9876543210'
    }).encode('utf-8')
    
    status, body = make_request(f"{base_url}/auth/register", register_data)
    print(f"Register Status: {status}")

    # 3. Login
    print("Logging in...")
    login_data = urllib.parse.urlencode({
        'csrf_token': csrf_token,
        'email': 'debug_login@example.com',
        'password': 'password123'
    }).encode('utf-8')
    
    status, body = make_request(f"{base_url}/auth/login", login_data)
    print(f"Login Status: {status}")
    
    if status == 200 and "dashboard" in body.lower():
        print("Login Successful!")
    elif status == 302:
        print("Login Redirected (Success)")
    else:
        print("Login Failed")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    reproduce_login_error(port)
