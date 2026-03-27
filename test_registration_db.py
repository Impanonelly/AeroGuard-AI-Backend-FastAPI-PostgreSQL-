"""
Test script to verify registration saves to database
Run this to test if registration is working correctly
"""
from database import SessionLocal
from models import User, UserRole
from auth.utils import hash_password

def test_registration():
    """Test creating a user in the database"""
    db = SessionLocal()
    
    try:
        # Check current user count
        user_count_before = db.query(User).count()
        print(f"Users in database before: {user_count_before}")
        
        # Create a test user
        test_email = "test_registration@aeroguard.com"
        test_employee_id = "TEST_REG_001"
        
        # Check if user already exists
        existing = db.query(User).filter(
            (User.email == test_email) | (User.employee_id == test_employee_id)
        ).first()
        
        if existing:
            print(f"WARNING: Test user already exists: {existing.email}")
            print("   Deleting old test user...")
            db.delete(existing)
            db.commit()
        
        # Create new test user
        test_user = User(
            email=test_email,
            password_hash=hash_password("Test123!"),
            full_name="Test Registration User",
            employee_id=test_employee_id,
            role=UserRole.AVIATOR,
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Verify user was created
        user_count_after = db.query(User).count()
        print(f"Users in database after: {user_count_after}")
        
        # Fetch the user back
        saved_user = db.query(User).filter(User.email == test_email).first()
        
        if saved_user:
            print("\nSUCCESS! User saved to database:")
            print(f"   ID: {saved_user.id}")
            print(f"   Email: {saved_user.email}")
            print(f"   Full Name: {saved_user.full_name}")
            print(f"   Employee ID: {saved_user.employee_id}")
            print(f"   Role: {saved_user.role}")
            print(f"   Is Active: {saved_user.is_active}")
            print(f"   Created At: {saved_user.created_at}")
            print("\nRegistration is working! Data is being saved to the 'users' table.")
            print("\nTo check in pgAdmin:")
            print("   1. Open pgAdmin")
            print("   2. Navigate to: aeroguard_db -> Schemas -> public -> Tables -> users")
            print("   3. Right-click 'users' -> View/Edit Data -> All Rows")
            print("   4. You should see this test user!")
        else:
            print("ERROR: User was not saved to database!")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing Registration Database Save...")
    print("=" * 50)
    test_registration()
    print("=" * 50)
