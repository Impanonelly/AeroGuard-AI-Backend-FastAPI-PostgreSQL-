import urllib.request
import json

def test_login(email, password):
    url = "http://localhost:8000/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Testing login for: {email}...")
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            if status == 200:
                print(f"SUCCESS: {email} logged in successfully.")
                print(f"Response: {json.dumps(json.loads(body), indent=2)}")
                return True
            else:
                print(f"FAILED: {email} login failed with status {status}")
                print(f"Response: {body}")
                return False
    except Exception as e:
        print(f"ERROR: Could not connect to backend. {e}")
        return False

if __name__ == "__main__":
    test_login("admin@aeroguard.ai", "admin123")