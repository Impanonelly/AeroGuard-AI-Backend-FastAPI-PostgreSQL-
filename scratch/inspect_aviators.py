import os
import sys
from datetime import datetime
from sqlalchemy import desc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import User, FitnessAssessment, AlcoholScreening, SubstanceScreening, UserRole, MedicalRecord
from database import SessionLocal

def inspect_aviators():
    db = SessionLocal()
    try:
        aviators = db.query(User).filter(User.role == UserRole.AVIATOR).all()
        print(f"Aviators in DB: {len(aviators)}")
        for aviator in aviators:
            # Latest Status
            latest_assessment = (
                db.query(FitnessAssessment)
                .filter(FitnessAssessment.user_id == aviator.id)
                .order_by(desc(FitnessAssessment.assessment_date))
                .first()
            )

            latest_alcohol = (
                db.query(AlcoholScreening)
                .filter(AlcoholScreening.user_id == aviator.id)
                .order_by(desc(AlcoholScreening.screening_date))
                .first()
            )
            alcohol_ok = latest_alcohol.result_status == "cleared" if latest_alcohol else False

            latest_substance = (
                db.query(SubstanceScreening)
                .filter(SubstanceScreening.user_id == aviator.id)
                .order_by(desc(SubstanceScreening.screening_date))
                .first()
            )
            substance_ok = latest_substance.result_status == "cleared" if latest_substance else False

            latest_medical = (
                db.query(MedicalRecord)
                .filter(MedicalRecord.user_id == aviator.id)
                .order_by(desc(MedicalRecord.record_date))
                .first()
            )
            medical_is_valid = False
            med_cert_status = "No Record"
            med_class = "None"
            med_valid_until = None
            med_limitations = None
            
            if latest_medical:
                med_class = latest_medical.medical_class or "None"
                med_valid_until = latest_medical.valid_until
                med_limitations = latest_medical.limitations
                if latest_medical.clearance_status == "cleared":
                    if not latest_medical.valid_until or latest_medical.valid_until >= datetime.utcnow():
                        medical_is_valid = True
                        med_cert_status = "Cleared / Valid Certificate"
                    else:
                        med_cert_status = "Expired Certificate"
                else:
                    med_cert_status = f"Restricted/Suspended ({latest_medical.clearance_status})"

            print(f"\nAviator ID: {aviator.id} | Name: {aviator.full_name} | Emp ID: {aviator.employee_id}")
            print(f"  Clearance Status: {latest_assessment.clearance_status if latest_assessment else 'N/A'}")
            print(f"  Risk Level: {latest_assessment.risk_level if latest_assessment else 'N/A'}")
            print(f"  Fatigue Score: {latest_assessment.fatigue_score if latest_assessment else 0}%")
            print(f"  Alcohol Cleared: {alcohol_ok} | Declared: {latest_assessment.alcohol_declared if latest_assessment else False}")
            print(f"  Medical Status: {med_cert_status} | Valid Until: {med_valid_until}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_aviators()
