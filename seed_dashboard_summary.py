import os
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

def seed_summary_and_alerts():
    db = SessionLocal()
    try:
        # Clear existing dashboard summary and alerts
        db.query(models.DashboardSummary).delete()
        db.query(models.Alert).delete()
        db.query(models.AlcoholTest).delete()
        db.query(models.DutyClearanceAction).delete()
        db.commit()

        print("--- Seeding DashboardSummary, Alerts, and AlcoholTests ---")

        # Query all aviators
        aviators = db.query(models.User).filter(models.User.role == "aviator").all()
        print(f"Found {len(aviators)} aviators.")

        for pilot in aviators:
            # Let's check their latest fitness assessment
            latest_fit = db.query(models.FitnessAssessment).filter(
                models.FitnessAssessment.user_id == pilot.id
            ).order_by(models.FitnessAssessment.id.desc()).first()

            # Determine values based on pilot id or latest fitness assessment
            if pilot.id == 11: # Emmanuel (Golden)
                status = "Cleared for Duty"
                fatigue = 12
                sleep = 8.2
                bac_status = "PASS"
                bac_val = 0.0
                alertness = 92
            elif pilot.id == 12: # Patrick (High Risk)
                status = "Conditional"
                fatigue = 78
                sleep = 4.5
                bac_status = "PASS"
                bac_val = 0.0
                alertness = 35
                
                # Seed an alert for Patrick
                alert1 = models.Alert(
                    user_id=pilot.id,
                    title="High Fatigue Risk Flagged",
                    description="AI model flagged Patrick with high fatigue risk (sleep debt: 3.5h). Supervisor review required.",
                    time_ago="10 minutes ago",
                    type="fatigue",
                    is_read=False
                )
                db.add(alert1)
            elif pilot.id == 13: # Grace (Grounded/Substance Violation)
                status = "Not Fit for Duty"
                fatigue = 92
                sleep = 3.0
                bac_status = "FAIL"
                bac_val = 0.03
                alertness = 15
                
                # Seed an alert and an alcohol test for Grace
                alert2 = models.Alert(
                    user_id=pilot.id,
                    title="Substance screening lockout",
                    description="CRITICAL: Positive BAC detected (0.03%). Dispatch Clearance Denied.",
                    time_ago="20 minutes ago",
                    type="alcohol",
                    is_read=False
                )
                db.add(alert2)
                
                test_grace = models.AlcoholTest(
                    user_id=pilot.id,
                    test_time="Today, 08:15 AM",
                    bac_percentage=0.03,
                    result="FAIL",
                    method="Manual",
                    device_info="Manual Registry",
                    screening_type="Pre-Flight",
                    medical_officer="Dr. Jean HABIMANA",
                    medical_recommendation="Ground Crew Member",
                    notes="Observed BAC level above limit (0.02% threshold). Enforced regulatory grounding."
                )
                db.add(test_grace)
            else:
                # Default for other aviators
                status = "Cleared for Duty"
                fatigue = 15
                sleep = 7.8
                bac_status = "PASS"
                bac_val = 0.0
                alertness = 85

            summary = models.DashboardSummary(
                user_id=pilot.id,
                readiness_status=status,
                fatigue_score=fatigue,
                sleep_hours=sleep,
                bac_status=bac_status,
                bac_percentage=bac_val,
                alertness_score=alertness
            )
            db.add(summary)

        db.commit()
        print("Successfully seeded DashboardSummary, Alerts, and AlcoholTests!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_summary_and_alerts()
