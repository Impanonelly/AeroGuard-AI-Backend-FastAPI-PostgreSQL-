import sys
import os

# Ensure we can import from the backend directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, UserRole, AlcoholScreening, FitnessAssessment, AuditLog
from auth.utils import hash_password
from datetime import datetime, timedelta

def seed_data():
    db = SessionLocal()
    try:
        # 1. Clean up existing test assessments to avoid clutter if re-run
        # db.query(FitnessAssessment).delete()
        # db.query(AlcoholScreening).delete()
        # Note: We won't delete users to avoid breaking authentication if user already logged in
        
        # 2. Add specific users for the demo scenarios
        users_to_add = [
            {
                "email": "john.cleared@aeroguard.com",
                "full_name": "Capt. John MUGABO (Cleared)",
                "employee_id": "AKG-P-201",
                "role": UserRole.AVIATOR,
                "license_number": "RW-ATPL-201"
            },
            {
                "email": "sarah.conditional@aeroguard.com",
                "full_name": "F/O Sarah UWASE (Conditional)",
                "employee_id": "AKG-P-202",
                "role": UserRole.AVIATOR,
                "license_number": "RW-CPL-202"
            },
            {
                "email": "mary.grounded@aeroguard.com",
                "full_name": "F/O Mary KAMIKAZI (Grounded)",
                "employee_id": "AKG-P-203",
                "role": UserRole.AVIATOR,
                "license_number": "RW-CPL-203"
            },
            {
                "email": "david.fatigue@aeroguard.com",
                "full_name": "Capt. David NKUSI (High Fatigue)",
                "employee_id": "AKG-P-204",
                "role": UserRole.AVIATOR,
                "license_number": "RW-ATPL-204"
            }
        ]
        
        user_map = {}
        for u_data in users_to_add:
            user = db.query(User).filter(User.email == u_data["email"]).first()
            if not user:
                user = User(
                    email=u_data["email"],
                    password_hash=hash_password("Password123!"),
                    full_name=u_data["full_name"],
                    employee_id=u_data["employee_id"],
                    role=u_data["role"],
                    license_number=u_data.get("license_number"),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            user_map[u_data["employee_id"]] = user

        now = datetime.utcnow()

        # 3. Create Scenarios
        
        # Scenario 1: Fully Cleared (John)
        u_john = user_map["AKG-P-201"]
        fa_john = FitnessAssessment(
            user_id=u_john.id,
            assessment_date=now - timedelta(hours=1),
            overall_score=94.5,
            health_score=98.0,
            fatigue_score=92.0,
            alcohol_substance_score=100.0,
            psychological_score=95.0,
            stress_score=90.0,
            risk_level="LOW",
            alertness_level="high",
            fit_for_duty=True,
            clearance_status="cleared",
            clearance_level="green",
            restrictions='[]',
            assessed_by="Dr. Amina UWIMANA",
            valid_until=now + timedelta(hours=11),
            flight_number="RAG-101",
            supervisor_override=False,
            ai_confidence_score=98.5,
            notes="Optimal condition for flight."
        )
        db.add(fa_john)

        # Scenario 2: Conditional Clearance (Sarah)
        u_sarah = user_map["AKG-P-202"]
        fa_sarah = FitnessAssessment(
            user_id=u_sarah.id,
            assessment_date=now - timedelta(hours=2),
            overall_score=72.0,
            health_score=85.0,
            fatigue_score=68.0, # Fatigue issue
            alcohol_substance_score=100.0,
            psychological_score=80.0,
            stress_score=75.0,
            risk_level="MEDIUM",
            alertness_level="moderate",
            fit_for_duty=True,
            clearance_status="conditional",
            clearance_level="yellow",
            restrictions='["Monitor fatigue during flight", "Maximum 6-hour duty period"]',
            assessed_by="Dr. Amina UWIMANA",
            valid_until=now + timedelta(hours=4),
            flight_number="RAG-102",
            supervisor_override=False,
            ai_confidence_score=92.0,
            notes="Moderate fatigue detected. Supervisor clearance required for long haul."
        )
        db.add(fa_sarah)

        # Scenario 3: Grounded due to Substance Violation (Mary)
        u_mary = user_map["AKG-P-203"]
        # Add the alcohol screening violation that caused it
        al_mary = AlcoholScreening(
            user_id=u_mary.id,
            screening_date=now - timedelta(minutes=45),
            bac_level=0.045,  # Above limit
            result_status="grounded",
            is_violation=True,
            violation_details="BAC above regulatory limit of 0.04%",
            test_method="breathalyzer"
        )
        db.add(al_mary)
        
        fa_mary = FitnessAssessment(
            user_id=u_mary.id,
            assessment_date=now - timedelta(minutes=30),
            overall_score=25.0,
            health_score=80.0,
            fatigue_score=70.0,
            alcohol_substance_score=0.0, # Failed substance
            psychological_score=60.0,
            stress_score=50.0,
            risk_level="CRITICAL",
            alertness_level="critical",
            fit_for_duty=False,
            clearance_status="grounded",
            clearance_level="red",
            restrictions='["GROUNDED - Alcohol/substance violation", "Mandatory counseling required"]',
            assessed_by="Automated Breathalyzer Kiosk",
            valid_until=None,
            flight_number=None,
            supervisor_override=False,
            ai_confidence_score=99.9,
            notes="Immediate grounding. Safety protocol initiated."
        )
        db.add(fa_mary)

        # Scenario 4: Grounded due to High Fatigue (David)
        u_david = user_map["AKG-P-204"]
        fa_david = FitnessAssessment(
            user_id=u_david.id,
            assessment_date=now - timedelta(minutes=10),
            overall_score=48.0,
            health_score=80.0,
            fatigue_score=35.0, # Severe fatigue
            alcohol_substance_score=100.0,
            psychological_score=70.0,
            stress_score=45.0,
            risk_level="HIGH",
            alertness_level="low",
            fit_for_duty=False,
            clearance_status="grounded",
            clearance_level="red",
            restrictions='["GROUNDED - High fatigue risk", "Minimum 10-hour rest required"]',
            assessed_by="AeroGuard AI",
            valid_until=None,
            flight_number=None,
            supervisor_override=False,
            ai_confidence_score=95.0,
            notes="Critical sleep debt detected. Unfit for operation."
        )
        db.add(fa_david)

        db.commit()
        print("Successfully seeded comprehensive demo scenarios for Operational Readiness Dashboards.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
