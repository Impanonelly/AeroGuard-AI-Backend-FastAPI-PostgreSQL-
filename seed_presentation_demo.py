import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, User, HealthRecord, AlcoholScreening, SubstanceScreening, DutyPeriod, FitnessAssessment, AlertnessReading, RiskPredictionLog, MedicalRecord
from auth.utils import hash_password

from database import SessionLocal

def seed():
    db = SessionLocal()
    try:
        db.query(AlertnessReading).delete()
        db.query(RiskPredictionLog).delete()
        db.query(FitnessAssessment).delete()
        db.query(DutyPeriod).delete()
        db.query(SubstanceScreening).delete()
        db.query(AlcoholScreening).delete()
        db.query(HealthRecord).delete()
        db.query(MedicalRecord).delete()
        db.query(User).filter(User.email.like("%@demo.com")).delete()
        db.commit()

        print("--- Seeding Presentation Demo Users ---")
        
        # 2. Create Users
        hashed = hash_password("Password123!")
        
        # User A: The "Golden" Pilot
        pilot_a = User(
            id=11,
            full_name="Capt. Emmanuel NIYONZIMA",
            email="emmanuel@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-101",
            is_active=True
        )
        
        # User B: The "High Risk" Pilot
        pilot_b = User(
            id=12,
            full_name="F/O Patrick MUGISHA",
            email="patrick@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-102",
            is_active=True
        )
        
        # User C: The "Grounded" Pilot
        pilot_c = User(
            id=13,
            full_name="Capt. Grace MUTESI",
            email="grace@demo.com",
            password_hash=hashed,
            role="aviator",
            employee_id="AG-103",
            is_active=True
        )

        db.add_all([pilot_a, pilot_b, pilot_c])
        db.commit()
        
        # Sync the primary key sequence in PostgreSQL to prevent future insertion collisions
        from sqlalchemy import text
        db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
        db.commit()

        db.refresh(pilot_a)
        db.refresh(pilot_b)
        db.refresh(pilot_c)

 
        # 2.5 Resolve or Create Supervisor / Medical Officer
        supervisor = db.query(User).filter(User.role.in_(["medical_officer", "supervisor", "safety_officer", "administrator"])).first()
        if not supervisor:
            supervisor = User(
                full_name="Dr. Jean HABIMANA",
                email="jean@aeroguard.com",
                password_hash=hashed,
                role="medical_officer",
                employee_id="AG-MED-01",
                is_active=True
            )
            db.add(supervisor)
            db.commit()
            db.refresh(supervisor)
            
        supervisor_id = supervisor.id

        # 3. Add Records for Pilot A (Golden)
        # Seed historical records (24 entries) to align metrics mathematically
        base_date = datetime.utcnow() - timedelta(days=25)
        for i in range(24):
            record_date = base_date + timedelta(days=i, hours=8)
            
            # 24 Health Records with complete vitals
            db.add(HealthRecord(
                user_id=pilot_a.id,
                record_date=record_date,
                heart_rate=64.0 + (i % 3),
                sleep_hours=8.2 if i == 23 else 7.5 + (i % 2) * 0.5,
                sleep_quality=88.0,
                stress_level=2.0,
                fatigue_score=12.0 if i == 23 else 15.0 - (i % 4),
                alertness_score=92.0 if i == 23 else 88.0 + (i % 5),
                blood_pressure_systolic=120.0 + (i % 5),
                blood_pressure_diastolic=80.0 + (i % 3),
                temperature=36.5 + (i % 4) * 0.1,
                oxygen_saturation=98.0 + (i % 2),
                respiratory_rate=14.0 + (i % 3)
            ))
            
            # 24 Alcohol Screenings (0.00% BAC, cleared)
            db.add(AlcoholScreening(
                user_id=pilot_a.id,
                screening_date=record_date,
                bac_level=0.0,
                result_status="cleared",
                is_violation=False,
                supervised_by=supervisor_id
            ))
            
            # 24 Duty Periods (completed, compliant rest hours before)
            db.add(DutyPeriod(
                user_id=pilot_a.id,
                duty_start=record_date + timedelta(hours=2),
                duty_end=record_date + timedelta(hours=10),
                duty_type="flight",
                status="completed",
                flight_number=f"AG-{100+i}",
                aircraft_type="B737",
                route="KGL-NBO",
                duty_hours=8.0,
                flight_hours=6.0,
                rest_hours_before=12.0, # Regulatory compliant (> 11.0 hours)
                alcohol_screening_completed=True,
                alcohol_screening_passed=True,
                fitness_assessment_completed=True,
                fitness_assessment_passed=True
            ))

            # 24 Fitness Assessments (overall score ~95, cleared, LOW risk)
            db.add(FitnessAssessment(
                user_id=pilot_a.id,
                assessment_date=record_date + timedelta(hours=1),
                overall_score=95.0 if i == 23 else 93.0 + (i % 3),
                health_score=96.0,
                fatigue_score=12.0 if i == 23 else 15.0,
                alcohol_substance_score=100.0,
                psychological_score=95.0,
                stress_score=90.0,
                risk_level="LOW",
                alertness_level="high" if i == 23 else "moderate",
                fit_for_duty=True,
                clearance_status="cleared",
                clearance_level="green"
            ))

        # Add single Substance Screening (negative, cleared)
        db.add(SubstanceScreening(
            user_id=pilot_a.id,
            screening_date=datetime.utcnow(),
            cannabis_result="negative", cocaine_result="negative", 
            opioids_result="negative", amphetamines_result="negative", benzodiazepines_result="negative",
            result_status="cleared", is_violation=False, supervised_by=supervisor_id
        ))

        # Add single Medical Record (Class 1 medical certificate, valid, cleared)
        db.add(MedicalRecord(
            user_id=pilot_a.id,
            record_date=datetime.utcnow() - timedelta(days=90),
            examination_type="annual",
            examining_physician="Dr. Jean HABIMANA",
            medical_facility="Kigali Aviation Medical Center",
            medical_class="Class 1",
            certificate_number="MC-2026-101",
            valid_from=datetime.utcnow() - timedelta(days=90),
            valid_until=datetime.utcnow() + timedelta(days=275),
            clearance_status="cleared",
            vision_ok=True,
            hearing_ok=True,
            cardiovascular_ok=True,
            neurological_ok=True,
            respiratory_ok=True,
            musculoskeletal_ok=True,
            psychiatric_ok=True,
            limitations="Must wear corrective lenses for distant vision",
            conditions="""[{"id": 1, "condition": "Mild Hypertension", "diagnosedDate": "2024-03-12", "severity": "Mild", "controlStatus": "controlled", "restrictions": ["Annual cardiovascular review required", "Blood pressure must remain under 140/90"]}]""",
            medications="""[{"id": 1, "name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "prescribedBy": "Dr. Jean HABIMANA", "flightSafetyWarning": false}]"""
        ))

        # Latest Alertness Reading (high alertness, matching score 92.0)
        db.add(AlertnessReading(
            user_id=pilot_a.id,
            reading_timestamp=datetime.utcnow(),
            source="manual",
            alertness_score=92.0,
            alertness_level="high",
            reaction_time_ms=240.0,
            
            risk_flag=False
        ))

        # Latest Risk Prediction Log (LOW risk, matching score 12.0)
        db.add(RiskPredictionLog(
            user_id=pilot_a.id,
            prediction_timestamp=datetime.utcnow(),
            sleep_hours_input=8.2,
            duty_hours_input=8.0,
            stress_level_input=2.0,
            alertness_score_input=92.0,
            heart_rate_input=64.0,
            reaction_time_input=240.0,
            predicted_risk_level="LOW",
            risk_score=12.0,
            confidence_score=95.0
        ))

        # 4. Add Records for Pilot B (High Risk - Fatigue)
        db.add(HealthRecord(
            user_id=pilot_b.id,
            record_date=datetime.utcnow(),
            heart_rate=88.0,
            sleep_hours=4.5,
            sleep_quality=40.0,
            stress_level=8.0,
            fatigue_score=78.0,
            alertness_score=35.0,
            blood_pressure_systolic=135.0,
            blood_pressure_diastolic=90.0,
            temperature=37.1,
            oxygen_saturation=96.0,
            respiratory_rate=18.0
        ))
        db.add(DutyPeriod(
            user_id=pilot_b.id,
            duty_start=datetime.utcnow() - timedelta(hours=12),
            duty_end=datetime.utcnow(),
            duty_type="flight",
            status="completed",
            flight_number="AG-999",
            aircraft_type="B737",
            route="KGL-DXB",
            duty_hours=12.5,
            flight_hours=9.0,
            rest_hours_before=6.0,
            alcohol_screening_completed=True,
            alcohol_screening_passed=True,
            fitness_assessment_completed=True,
            fitness_assessment_passed=False
        ))
        db.add(FitnessAssessment(
            user_id=pilot_b.id,
            assessment_date=datetime.utcnow(),
            overall_score=42, risk_level="HIGH", 
            clearance_status="conditional", fit_for_duty=False,
            notes="High fatigue detected. Mandatory rest period required."
        ))
        db.add(RiskPredictionLog(
            user_id=pilot_b.id,
            prediction_timestamp=datetime.utcnow(),
            sleep_hours_input=4.5,
            duty_hours_input=12.5,
            stress_level_input=8.0,
            alertness_score_input=35.0,
            heart_rate_input=88.0,
            reaction_time_input=380.0,
            predicted_risk_level="HIGH",
            risk_score=78.0,
            confidence_score=91.0
        ))

        # Add single Medical Record for Pilot B (Patrick MUGISHA)
        db.add(MedicalRecord(
            user_id=pilot_b.id,
            record_date=datetime.utcnow() - timedelta(days=60),
            examination_type="annual",
            examining_physician="Dr. Jean HABIMANA",
            medical_facility="Kigali Aviation Medical Center",
            medical_class="Class 1",
            certificate_number="MC-2026-102",
            valid_from=datetime.utcnow() - timedelta(days=60),
            valid_until=datetime.utcnow() + timedelta(days=305),
            clearance_status="cleared",
            vision_ok=True,
            hearing_ok=True,
            cardiovascular_ok=True,
            neurological_ok=True,
            respiratory_ok=True,
            musculoskeletal_ok=True,
            psychiatric_ok=True,
            limitations="Must wear corrective lenses for distant vision",
            conditions="""[{"id": 1, "condition": "Mild Hypertension", "diagnosedDate": "2024-03-12", "severity": "Mild", "controlStatus": "controlled", "restrictions": ["Annual cardiovascular review required", "Blood pressure must remain under 140/90"]}]""",
            medications="""[{"id": 1, "name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "prescribedBy": "Dr. Jean HABIMANA", "flightSafetyWarning": false}]"""
        ))


        # 5. Add Records for Pilot C (Grounded - Substance)
        db.add(HealthRecord(
            user_id=pilot_c.id,
            record_date=datetime.utcnow(),
            heart_rate=95.0,
            sleep_hours=3.0,
            sleep_quality=30.0,
            stress_level=9.5,
            fatigue_score=92.0,
            alertness_score=15.0,
            blood_pressure_systolic=142.0,
            blood_pressure_diastolic=95.0,
            temperature=37.4,
            oxygen_saturation=95.0,
            respiratory_rate=20.0
        ))
        db.add(DutyPeriod(
            user_id=pilot_c.id,
            duty_start=datetime.utcnow() - timedelta(hours=14),
            duty_end=datetime.utcnow(),
            duty_type="flight",
            status="completed",
            flight_number="AG-888",
            aircraft_type="B737",
            route="KGL-JNB",
            duty_hours=14.0,
            flight_hours=10.0,
            rest_hours_before=8.0,
            alcohol_screening_completed=True,
            alcohol_screening_passed=True,
            fitness_assessment_completed=True,
            fitness_assessment_passed=False
        ))
        db.add(SubstanceScreening(
            user_id=pilot_c.id,
            screening_date=datetime.utcnow(),
            cannabis_result="positive", cocaine_result="negative", 
            opioids_result="negative", amphetamines_result="negative", benzodiazepines_result="negative",
            result_status="grounded", is_violation=True, supervised_by=supervisor_id,
            violation_details="Positive result for Cannabis. Immediate grounding."
        ))
        db.add(RiskPredictionLog(
            user_id=pilot_c.id,
            prediction_timestamp=datetime.utcnow(),
            sleep_hours_input=3.0,
            duty_hours_input=14.0,
            stress_level_input=9.5,
            alertness_score_input=15.0,
            heart_rate_input=95.0,
            reaction_time_input=450.0,
            predicted_risk_level="CRITICAL",
            risk_score=95.0,
            confidence_score=93.0
        ))

        # Add single Medical Record for Pilot C (Grace MUTESI)
        db.add(MedicalRecord(
            user_id=pilot_c.id,
            record_date=datetime.utcnow() - timedelta(days=30),
            examination_type="periodic",
            examining_physician="Dr. Jean HABIMANA",
            medical_facility="Kigali Aviation Medical Center",
            medical_class="Class 1",
            certificate_number="MC-2026-103",
            valid_from=datetime.utcnow() - timedelta(days=30),
            valid_until=datetime.utcnow() - timedelta(days=1), # Expired yesterday/suspended
            clearance_status="suspended",
            vision_ok=True,
            hearing_ok=True,
            cardiovascular_ok=True,
            neurological_ok=True,
            respiratory_ok=True,
            musculoskeletal_ok=True,
            psychiatric_ok=True,
            limitations="Grounded due to substance abuse screening violation.",
            conditions="""[{"id": 1, "condition": "Substance Use Disorder - Cannabis", "diagnosedDate": "2026-06-01", "severity": "Moderate", "controlStatus": "uncontrolled", "restrictions": ["Mandatory rehabilitation referral", "Subject to random testing upon reinstatement"]}]""",
            medications="""[]"""
        ))


        # 6. Seed other aviators (if any) with realistic low-to-medium risk scores
        other_aviators = db.query(User).filter(User.role == "aviator", ~User.email.like("%@demo.com")).all()
        print(f"Seeding health and risk data for {len(other_aviators)} other aviators...")
        
        # Calibrated distribution (4 pilots get 12.0, 4 pilots get 15.0, 4 pilots get 20.0)
        # yielding a fleet average of exactly ~25.0.
        for idx, pilot in enumerate(other_aviators):
            tier = idx % 3
            if tier == 0:
                score = 12.0
                sleep = 8.0
                stress = 2.0
                duty = 6.0
                alertness = 90.0
            elif tier == 1:
                score = 15.5
                sleep = 7.5
                stress = 3.0
                duty = 8.0
                alertness = 85.0
            else:
                score = 20.0
                sleep = 7.0
                stress = 4.0
                duty = 9.0
                alertness = 80.0
                
            # HealthRecord
            db.add(HealthRecord(
                user_id=pilot.id,
                record_date=datetime.utcnow(),
                heart_rate=68.0 + idx,
                sleep_hours=sleep,
                sleep_quality=75.0 + idx,
                stress_level=stress,
                fatigue_score=100.0 - alertness,
                alertness_score=alertness,
                blood_pressure_systolic=120.0,
                blood_pressure_diastolic=80.0,
                temperature=36.6,
                oxygen_saturation=98.0,
                respiratory_rate=14.0
            ))
            
            # DutyPeriod
            db.add(DutyPeriod(
                user_id=pilot.id,
                duty_start=datetime.utcnow() - timedelta(hours=int(duty) + 2),
                duty_end=datetime.utcnow() - timedelta(hours=2),
                duty_type="flight",
                status="completed",
                flight_number=f"AG-O{200+idx}",
                aircraft_type="B737",
                route="KGL-EBB",
                duty_hours=duty,
                flight_hours=duty - 1.0,
                rest_hours_before=12.0,
                alcohol_screening_completed=True,
                alcohol_screening_passed=True,
                fitness_assessment_completed=True,
                fitness_assessment_passed=True
            ))
            
            # FitnessAssessment
            db.add(FitnessAssessment(
                user_id=pilot.id,
                assessment_date=datetime.utcnow(),
                overall_score=100.0 - score,
                health_score=90.0,
                fatigue_score=100.0 - alertness,
                alcohol_substance_score=100.0,
                psychological_score=92.0,
                stress_score=90.0,
                risk_level="LOW",
                alertness_level="high",
                fit_for_duty=True,
                clearance_status="cleared",
                clearance_level="green"
            ))
            
            # RiskPredictionLog
            db.add(RiskPredictionLog(
                user_id=pilot.id,
                prediction_timestamp=datetime.utcnow(),
                sleep_hours_input=sleep,
                duty_hours_input=duty,
                stress_level_input=stress,
                alertness_score_input=alertness,
                heart_rate_input=68.0 + idx,
                reaction_time_input=250.0 + idx * 5,
                predicted_risk_level="LOW",
                risk_score=score,
                confidence_score=92.0
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
