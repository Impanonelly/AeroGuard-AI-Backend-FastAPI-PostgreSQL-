import sys
import os
from database import Base, engine
# Import all models to ensure they are registered
from models import User, UserSecurityKey, HealthRecord, AlcoholScreening, SubstanceScreening, DutyPeriod, FitnessAssessment, AuditLog, Notification

def reset_db():
    print("--- Resetting Database for Presentation ---")
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables.")
    Base.metadata.create_all(bind=engine)
    print("Recreated all tables with updated schema.")

if __name__ == "__main__":
    reset_db()
