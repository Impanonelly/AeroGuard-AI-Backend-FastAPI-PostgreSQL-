from database import SessionLocal
from models import User, UserRole, AlcoholScreening
from auth.utils import hash_password
from datetime import datetime, timedelta

def seed_data():
    db = SessionLocal()
    try:
        # Create additional users
        users_to_add = [
            {
                "email": "robert@aeroguard.com",
                "full_name": "Capt. Robert SAFARI",
                "employee_id": "AKG-P-101",
                "role": UserRole.SUPERVISOR,
                "license_number": "RW-ATPL-101"
            },
            {
                "email": "mary@aeroguard.com",
                "full_name": "F/O Mary KAMIKAZI",
                "employee_id": "AKG-P-102",
                "role": UserRole.AVIATOR,
                "license_number": "RW-CPL-102"
            },
            {
                "email": "jean@aeroguard.com",
                "full_name": "Dr. Jean HABIMANA",
                "employee_id": "AKG-S-001",
                "role": UserRole.SAFETY_OFFICER,
                "license_number": "MED-RW-001"
            }
        ]
        
        created_users = []
        for u_data in users_to_add:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                new_user = User(
                    email=u_data["email"],
                    password_hash=hash_password("Password123!"),
                    full_name=u_data["full_name"],
                    employee_id=u_data["employee_id"],
                    role=u_data["role"],
                    license_number=u_data.get("license_number"),
                    is_active=True
                )
                db.add(new_user)
                created_users.append(new_user)
        
        db.commit()
        for u in created_users:
            db.refresh(u)
        
        # Get all aviators (including existing ones)
        aviators = db.query(User).filter(User.role == UserRole.AVIATOR).all()
        
        # Add some alcohol screenings
        for aviator in aviators:
            # Add a cleared test for today
            screening = AlcoholScreening(
                user_id=aviator.id,
                screening_date=datetime.utcnow() - timedelta(hours=2),
                bac_level=0.000,
                result_status="cleared",
                is_violation=False,
                test_method="breathalyzer"
            )
            db.add(screening)
            
        # Add one violation for drama
        if aviators:
            violation = AlcoholScreening(
                user_id=aviators[0].id,
                screening_date=datetime.utcnow() - timedelta(minutes=30),
                bac_level=0.045,
                result_status="grounded",
                is_violation=True,
                violation_details="BAC above regulatory limit of 0.04%",
                test_method="breathalyzer"
            )
            db.add(violation)
            
        db.commit()
        print("Successfully seeded users and safety events.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
