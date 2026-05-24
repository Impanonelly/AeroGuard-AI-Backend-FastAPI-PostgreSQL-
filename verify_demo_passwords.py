from database import SessionLocal
from models import User
from auth.utils import verify_password

def verify_credentials():
    db = SessionLocal()
    emails = ["emmanuel@demo.com", "patrick@demo.com", "grace@demo.com", "robert@aeroguard.com"]
    password_to_check = "Password123!"
    
    print("Checking Demo Accounts:")
    print("=" * 60)
    for email in emails:
        user = db.query(User).filter(User.email == email).first()
        if user:
            is_valid = verify_password(password_to_check, user.password_hash)
            print(f"Email: {email:<25} | Name: {user.full_name:<25} | PW Valid: {is_valid}")
        else:
            print(f"Email: {email:<25} | NOT FOUND in database!")
    db.close()

if __name__ == "__main__":
    verify_credentials()
