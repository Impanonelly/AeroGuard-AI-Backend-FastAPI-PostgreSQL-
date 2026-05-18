import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, User, HealthRecord, AlcoholScreening, SubstanceScreening, DutyPeriod, FitnessAssessment
from auth.utils import hash_password

# Database Configuration (ensure this matches your .env)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/aeroguard_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()
    try:
        # 1. Clear existing demo data
        db.query(FitnessAssessment).delete()
        db.query(DutyPeriod).delete()
        db.query(SubstanceScreening).delete()
        db.query(AlcoholScreening).delete()
        db.query(HealthRecord).delete()
        db.query(User).filter(User.email.like("%@demo.com")).delete()
        db.commit()

        print("--- Seeding Presentation Demo Users ---")
        
        # 2. Create Users
        hashed = hash_password("Password123!")
        
        # User A: The "Golden" Pilot
        pilot_a = User(
            full_name="Capt. Emmanuel NIYONZIMA",
            email="emmanuel@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-101",
            is_active=True
        )
        
        # User B: The "High Risk" Pilot
        pilot_b = User(
            full_name="F/O Patrick MUGISHA",
            email="patrick@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-102",
            is_active=True
        )
        
        # User C: The "Grounded" Pilot
        pilot_c = User(
            full_name="Capt. Grace MUTESI",
            email="grace@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-103",
            is_active=True
        )

        db.add_all([pilot_a, pilot_b, pilot_c])
        db.commit()
        db.refresh(pilot_a)
        db.refresh(pilot_b)
        db.refresh(pilot_c)

        # 3. Add Records for Pilot A (Golden)
        db.add(AlcoholScreening(user_id=pilot_a.id, bac_level=0.0, result_status="cleared"))
        db.add(SubstanceScreening(
            user_id=pilot_a.id, cannabis_result="negative", cocaine_result="negative", 
            opioids_result="negative", amphetamines_result="negative", benzodiazepines_result="negative",
            result_status="cleared", is_violation=False, supervised_by=1
        ))
        db.add(FitnessAssessment(
            user_id=pilot_a.id, overall_score=95, risk_level="LOW", 
            clearance_status="cleared", fit_for_duty=True
        ))

        # 4. Add Records for Pilot B (High Risk - Fatigue)
        db.add(FitnessAssessment(
            user_id=pilot_b.id, overall_score=42, risk_level="HIGH", 
            clearance_status="conditional", fit_for_duty=False,
            notes="High fatigue detected. Mandatory rest period required."
        ))

        # 5. Add Records for Pilot C (Grounded - Substance)
        db.add(SubstanceScreening(
            user_id=pilot_c.id, cannabis_result="positive", cocaine_result="negative", 
            opioids_result="negative", amphetamines_result="negative", benzodiazepines_result="negative",
            result_status="grounded", is_violation=True, supervised_by=1,
            violation_details="Positive result for Cannabis. Immediate grounding."
        ))

        db.commit()
        print("Database successfully seeded for presentation!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
