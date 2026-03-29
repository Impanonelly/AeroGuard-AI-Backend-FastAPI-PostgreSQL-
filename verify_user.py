from database import SessionLocal
from models import User

def check_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "testpilot@aeroguard.com").first()
        if user:
            print(f"FOUND: User {user.full_name} ({user.email}) exists with role {user.role}.")
            print(f"Created at: {user.created_at}")
        else:
            print("NOT FOUND: User testpilot@aeroguard.com does not exist in the database.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
