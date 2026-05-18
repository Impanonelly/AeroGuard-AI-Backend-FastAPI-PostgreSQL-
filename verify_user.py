from database import SessionLocal
from models import User
from auth.utils import verify_password

def check_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User found: {user.full_name}")
            print(f"Role: {user.role}")
            print(f"Is Active: {user.is_active}")
            
            password_to_check = "Password123!"
            is_valid = verify_password(password_to_check, user.password_hash)
            print(f"Password 'Password123!' is valid: {is_valid}")
        else:
            print(f"User {email} not found.")
    finally:
        db.close()

if __name__ == "__main__":
    check_user("patrick.mugisha@aeroguard.com")
