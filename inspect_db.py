import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import Base, User, HealthRecord, AlcoholScreening, SubstanceScreening, DutyPeriod, FitnessAssessment, AlertnessReading, RiskPredictionLog, MedicalRecord
from database import SessionLocal

def inspect():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"User ID: {u.id} | Email: {u.email} | Name: {u.full_name} | Role: {u.role}")
        
        preds = db.query(RiskPredictionLog).all()
        print(f"\nTotal Risk Prediction Logs: {len(preds)}")
        for p in preds:
            print(f"Pred ID: {p.id} | User ID: {p.user_id} | Risk: {p.predicted_risk_level} | Score: {p.risk_score}")
            
        fit = db.query(FitnessAssessment).all()
        print(f"\nTotal Fitness Assessments: {len(fit)}")
        for f in fit:
            print(f"Fit ID: {f.id} | User ID: {f.user_id} | Risk: {f.risk_level} | Score: {f.overall_score} | Fit: {f.fit_for_duty}")
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
