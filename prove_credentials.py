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
    except urllib.error.HTTPError as e:
        print(f"FAILED: {email} login failed with status {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Test a few demo users
    test_login("robert@aeroguard.com", "Password123!")
    print("-" * 50)
    test_login("mary@aeroguard.com", "Password123!")
    print("-" * 50)
    test_login("testpilot@aeroguard.com", "Password123!")
