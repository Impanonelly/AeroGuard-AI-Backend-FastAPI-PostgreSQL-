from database import SessionLocal
from models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"{'ID':<5} | {'Name':<20} | {'Email':<30} | {'Role':<15}")
        print("-" * 75)
        for u in users:
            print(f"{u.id:<5} | {u.full_name:<20} | {u.email:<30} | {u.role:<15}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
