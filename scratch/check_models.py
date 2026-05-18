from database import SessionLocal
from models import User, HealthRecord

def test():
    try:
        db = SessionLocal()
        user = db.query(User).first()
        if user:
            print(f"User found: {user.full_name}")
            # Try to access a relationship
            print(f"Health records count: {len(user.health_records)}")
        db.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test()
