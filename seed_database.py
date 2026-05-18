"""
AeroGuard AI — Full Demo Data Seeder
Seeds pilots, users, health records, alcohol screenings, duty periods, fitness assessments
Run: python seed_database.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
from models import Base, Pilot, User, HealthRecord, AlcoholScreening, DutyPeriod, FitnessAssessment, AuditLog, IoTDevice, MedicalRecord
from auth.utils import hash_password
from datetime import datetime, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("[START] AeroGuard AI - Database Seeder")
print("=" * 50)

# ─── USERS ──────────────────────────────────────────────────────────────────
print("\n[USERS] Seeding Users...")

USERS = [
    { "email": "jean@aeroguard.com",   "full_name": "Dr. Jean HABIMANA",   "employee_id": "MED-003", "role": "medical_officer",  "license": "MED-2024-001" },
    { "email": "robert@aeroguard.com", "full_name": "Robert SAFARI",        "employee_id": "SAF-001", "role": "safety_officer",   "license": "SAF-2024-001" },
    { "email": "mary@aeroguard.com",   "full_name": "Mary KAMIKAZI",         "employee_id": "SAF-002", "role": "safety_officer",   "license": "SAF-2024-002" },
    { "email": "admin@aeroguard.com",  "full_name": "Admin SYSTEM",          "employee_id": "ADM-001", "role": "administrator",    "license": None },
    { "email": "grace@aeroguard.com",  "full_name": "Grace MUTESI",          "employee_id": "SUP-001", "role": "supervisor",       "license": None },
    { "email": "david@aeroguard.com",  "full_name": "David NKUSI",           "employee_id": "AKG-015", "role": "aviator",          "license": "LIC-2024-015" },
    { "email": "sarah@aeroguard.com",  "full_name": "F/O Sarah UWASE",       "employee_id": "AKG-042", "role": "aviator",          "license": "LIC-2024-042" },
    { "email": "john@aeroguard.com",   "full_name": "Capt. John MUGABO",     "employee_id": "AKG-001", "role": "aviator",          "license": "LIC-2024-001" },
    { "email": "alice@aeroguard.com",  "full_name": "Capt. Alice UWIMANA",   "employee_id": "AKG-022", "role": "aviator",          "license": "LIC-2024-022" },
    { "email": "emmanuel@aeroguard.com","full_name": "Capt. Emmanuel HABIMANA","employee_id":"AKG-033","role": "aviator",          "license": "LIC-2024-033" },
]

created_users = []
for u in USERS:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if existing:
        print(f"   [OK] Skipping {u['email']} (already exists)")
        created_users.append(existing)
        continue
    user = User(
        email=u["email"],
        full_name=u["full_name"],
        employee_id=u["employee_id"],
        role=u["role"],
        license_number=u.get("license"),
        password_hash=hash_password("Password123!"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.flush()
    created_users.append(user)
    print(f"   [DONE] Created: {u['full_name']} ({u['role']})")

db.commit()

# ─── PILOTS ─────────────────────────────────────────────────────────────────
print("\n[PILOTS] Seeding Pilots...")

PILOTS = [
    { "name": "Capt. John MUGABO",      "email": "john.pilot@aeroguard.com",    "employee_id": "AKG-P-001", "role": "Captain",       "sleep": 7.5, "duty": 4.2,  "stress": 3.0, "reaction": 88, "alertness": 85, "risk": "LOW" },
    { "name": "F/O Mary KAMIKAZI",       "email": "mary.pilot@aeroguard.com",    "employee_id": "AKG-P-042", "role": "First Officer", "sleep": 5.5, "duty": 9.0,  "stress": 6.0, "reaction": 70, "alertness": 58, "risk": "MEDIUM" },
    { "name": "Capt. David NKUSI",       "email": "david.pilot@aeroguard.com",   "employee_id": "AKG-P-015", "role": "Captain",       "sleep": 4.0, "duty": 11.0, "stress": 8.5, "reaction": 55, "alertness": 22, "risk": "HIGH" },
    { "name": "Capt. Alice UWIMANA",     "email": "alice.pilot@aeroguard.com",   "employee_id": "AKG-P-022", "role": "Captain",       "sleep": 8.0, "duty": 3.5,  "stress": 2.0, "reaction": 92, "alertness": 90, "risk": "LOW" },
    { "name": "Capt. Emmanuel HABIMANA", "email": "emma.pilot@aeroguard.com",    "employee_id": "AKG-P-033", "role": "Captain",       "sleep": 7.0, "duty": 5.0,  "stress": 3.5, "reaction": 84, "alertness": 80, "risk": "LOW" },
    { "name": "F/O Sarah UWASE",         "email": "sarah.pilot@aeroguard.com",   "employee_id": "AKG-P-044", "role": "First Officer", "sleep": 6.0, "duty": 7.5,  "stress": 5.0, "reaction": 76, "alertness": 68, "risk": "MEDIUM" },
    { "name": "Capt. Robert SAFARI",     "email": "robert.pilot@aeroguard.com",  "employee_id": "AKG-P-005", "role": "Captain",       "sleep": 7.8, "duty": 4.0,  "stress": 2.5, "reaction": 90, "alertness": 88, "risk": "LOW" },
    { "name": "F/O Jean MUGISHA",        "email": "jean.pilot@aeroguard.com",    "employee_id": "AKG-P-055", "role": "First Officer", "sleep": 5.0, "duty": 10.0, "stress": 7.0, "reaction": 60, "alertness": 45, "risk": "HIGH" },
    { "name": "Capt. Grace INGABIRE",    "email": "grace.pilot@aeroguard.com",   "employee_id": "AKG-P-061", "role": "Captain",       "sleep": 8.5, "duty": 2.0,  "stress": 1.5, "reaction": 95, "alertness": 93, "risk": "LOW" },
    { "name": "F/O Patrick NDIKUMANA",   "email": "patrick.pilot@aeroguard.com", "employee_id": "AKG-P-078", "role": "First Officer", "sleep": 6.5, "duty": 6.0,  "stress": 4.5, "reaction": 78, "alertness": 72, "risk": "LOW" },
]

for p in PILOTS:
    existing = db.query(Pilot).filter(Pilot.employee_id == p["employee_id"]).first()
    if existing:
        print(f"   [OK] Skipping {p['name']} (already exists)")
        continue
    pilot = Pilot(
        name=p["name"], email=p["email"], employee_id=p["employee_id"], role=p["role"],
        sleep_hours=p["sleep"], duty_hours=p["duty"], stress_level=p["stress"],
        reaction_score=p["reaction"], alertness_score=p["alertness"], risk_level=p["risk"],
        created_at=datetime.utcnow(),
    )
    db.add(pilot)
    print(f"   [DONE] Created: {p['name']} (Risk: {p['risk']})")

db.commit()

# ─── HEALTH RECORDS ─────────────────────────────────────────────────────────
print("\n[HEALTH] Seeding Health Records...")

aviator_users = [u for u in created_users if u.role == "aviator"]
if aviator_users:
    for user in aviator_users[:5]:
        for days_ago in [0, 7, 14]:
            rec_date = datetime.utcnow() - timedelta(days=days_ago)
            existing = db.query(HealthRecord).filter(
                HealthRecord.user_id == user.id,
                HealthRecord.record_date >= rec_date.replace(hour=0, minute=0)
            ).first()
            if existing:
                continue
            rec = HealthRecord(
                user_id=user.id,
                record_date=rec_date,
                heart_rate=random.uniform(60, 85),
                blood_pressure_systolic=random.uniform(110, 130),
                blood_pressure_diastolic=random.uniform(70, 85),
                temperature=36.5 + random.uniform(-0.3, 0.5),
                oxygen_saturation=random.uniform(96, 99),
                sleep_hours=random.uniform(5, 9),
                sleep_quality=random.uniform(60, 95),
                stress_level=random.uniform(2, 7),
                fatigue_score=random.uniform(50, 90),
                alertness_score=random.uniform(55, 95),
                cognitive_score=random.uniform(70, 95),
                created_at=rec_date,
            )
            db.add(rec)
    db.commit()
    print(f"   [DONE] Created health records for {len(aviator_users[:5])} aviators")
else:
    print("   ⚠️  No aviator users found, skipping health records")

# ─── ALCOHOL SCREENINGS ─────────────────────────────────────────────────────
print("\n[ALCOHOL] Seeding Alcohol Screenings...")

screening_data = [
    { "uid": 1, "bac": 0.000, "result": "cleared",  "type": "pre_flight",  "is_viol": False },
    { "uid": 2, "bac": 0.000, "result": "cleared",  "type": "pre_flight",  "is_viol": False },
    { "uid": 3, "bac": 0.030, "result": "grounded", "type": "pre_flight",  "is_viol": True,  "details": "BAC exceeds 0.02% limit. Grounding initiated." },
    { "uid": 4, "bac": 0.000, "result": "cleared",  "type": "pre_flight",  "is_viol": False },
    { "uid": 5, "bac": 0.000, "result": "cleared",  "type": "pre_flight",  "is_viol": False },
    { "uid": 6, "bac": 0.000, "result": "cleared",  "type": "random",      "is_viol": False },
    { "uid": 7, "bac": 0.000, "result": "cleared",  "type": "post_flight", "is_viol": False },
]

for s in screening_data:
    if s["uid"] > len(created_users):
        continue
    user = created_users[s["uid"] - 1]
    if not db.query(AlcoholScreening).filter(AlcoholScreening.user_id == user.id).first():
        rec = AlcoholScreening(
            user_id=user.id,
            screening_date=datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
            screening_type=s["type"],
            bac_level=s["bac"],
            result_status=s["result"],
            is_violation=s["is_viol"],
            violation_details=s.get("details"),
            witness_name="Safety Officer on duty",
            test_location="Pre-flight screening bay",
            created_at=datetime.utcnow(),
        )
        db.add(rec)
db.commit()
print(f"   [DONE] Created {len(screening_data)} alcohol screening records")

# ─── DUTY PERIODS ───────────────────────────────────────────────────────────
print("\n[DUTY] Seeding Duty Periods...")

routes = [("KGL", "NBI", "RVA101"), ("KGL", "ADD", "RVA201"), ("KGL", "JRO", "RVA301"), ("KGL", "DAR", "RVA401")]
for i, user in enumerate(created_users[:6]):
    if not db.query(DutyPeriod).filter(DutyPeriod.user_id == user.id).first():
        route = routes[i % len(routes)]
        start = datetime.utcnow() - timedelta(hours=random.randint(2, 8))
        duty = DutyPeriod(
            user_id=user.id,
            duty_start=start,
            duty_end=start + timedelta(hours=random.uniform(2, 6)),
            duty_type="flight",
            status="completed",
            flight_number=route[2],
            aircraft_type="Bombardier Q400",
            route=f"{route[0]}-{route[1]}",
            departure_airport=route[0],
            arrival_airport=route[1],
            duty_hours=random.uniform(3, 8),
            rest_hours_before=random.uniform(8, 14),
            alcohol_screening_completed=True,
            alcohol_screening_passed=True,
            fitness_assessment_completed=True,
            fitness_assessment_passed=True,
        )
        db.add(duty)
db.commit()
print(f"   [DONE] Created duty period records")

# ─── FITNESS ASSESSMENTS ────────────────────────────────────────────────────
print("\n[FITNESS] Seeding Fitness Assessments...")

fitness_data = [
    { "score": 88, "health": 90, "fatigue": 85, "clearance": "cleared",     "risk": "LOW",    "level": "green" },
    { "score": 62, "health": 75, "fatigue": 55, "clearance": "conditional", "risk": "MEDIUM", "level": "yellow" },
    { "score": 25, "health": 60, "fatigue": 20, "clearance": "grounded",    "risk": "HIGH",   "level": "red" },
    { "score": 92, "health": 95, "fatigue": 90, "clearance": "cleared",     "risk": "LOW",    "level": "green" },
    { "score": 79, "health": 82, "fatigue": 78, "clearance": "cleared",     "risk": "LOW",    "level": "green" },
]

for i, fd in enumerate(fitness_data):
    if i >= len(created_users):
        break
    user = created_users[i]
    if not db.query(FitnessAssessment).filter(FitnessAssessment.user_id == user.id).first():
        fa = FitnessAssessment(
            user_id=user.id,
            assessment_date=datetime.utcnow(),
            overall_score=fd["score"],
            health_score=fd["health"],
            fatigue_score=fd["fatigue"],
            alcohol_substance_score=100.0,
            psychological_score=random.uniform(70, 95),
            stress_score=random.uniform(55, 85),
            risk_level=fd["risk"],
            fit_for_duty=(fd["clearance"] == "cleared"),
            clearance_status=fd["clearance"],
            clearance_level=fd["level"],
            assessed_by="AeroGuard AI System v1.0",
            valid_until=datetime.utcnow() + timedelta(hours=12),
            ai_confidence_score=random.uniform(85, 99),
        )
        db.add(fa)
db.commit()
print(f"   [DONE] Created fitness assessment records")

# ─── AUDIT LOGS ─────────────────────────────────────────────────────────────
print("\n[AUDIT] Seeding Audit Logs...")
audit_actions = [
    ("login", "user", "User logged in successfully"),
    ("view", "assessment", "Viewed fitness assessment"),
    ("submit", "alcohol_screening", "Submitted pre-flight BAC screening"),
    ("update", "duty_period", "Updated duty period record"),
]
for user in created_users[:4]:
    for action, resource, detail in audit_actions:
        if not db.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.action_type == action).first():
            log = AuditLog(
                user_id=user.id,
                action_type=action,
                resource_type=resource,
                action_details=detail,
                module="aeroguard_ai",
                success=True,
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(5, 200)),
            )
            db.add(log)
db.commit()
print(f"   [DONE] Created audit log entries")

# ─── IOT DEVICES ────────────────────────────────────────────────────────────
print("\n[IOT] Seeding IoT Devices...")
iot_devices_data = [
    {"name": "AeroGuard Mobile App", "type": "Smartphone Sensor Hub", "status": "online", "battery": 85, "device_id": "IOT-APP-001"},
    {"name": "Xiaomi Smart Band 8", "type": "Basic Fitness Wearable", "status": "online", "battery": 92, "device_id": "IOT-BAND-001"},
    {"name": "BACtrack C6", "type": "Consumer Breathalyzer", "status": "online", "battery": 64, "device_id": "IOT-BAC-001"},
    {"name": "Fitbit Inspire 3", "type": "Sleep Tracker", "status": "online", "battery": 100, "device_id": "IOT-FIT-001"},
    {"name": "Generic Bluetooth Webcam", "type": "Eye Tracking Sensor", "status": "warning", "battery": 100, "device_id": "IOT-CAM-001"},
]
for d in iot_devices_data:
    if not db.query(IoTDevice).filter(IoTDevice.device_id == d["device_id"]).first():
        iot = IoTDevice(
            name=d["name"], type=d["type"], status=d["status"], battery=d["battery"], device_id=d["device_id"],
            created_at=datetime.utcnow()
        )
        db.add(iot)
db.commit()
print(f"   [DONE] Created IoT Devices")

# ─── MEDICAL RECORDS ────────────────────────────────────────────────────────
print("\n[MEDICAL] Seeding RCAA Medical Records...")

# Fetch seeded aviator users
aviators_map = {u.email: u for u in created_users if u.role == "aviator"}

if aviators_map:
    # 1. Capt. John MUGABO (john@aeroguard.com) - Active Class 1
    if "john@aeroguard.com" in aviators_map:
        john = aviators_map["john@aeroguard.com"]
        if not db.query(MedicalRecord).filter(MedicalRecord.user_id == john.id).first():
            rec = MedicalRecord(
                user_id=john.id,
                record_date=datetime.utcnow() - timedelta(days=180),
                examination_type="annual",
                examining_physician="Dr. Jean HABIMANA",
                medical_facility="Akagera Aviation Health Center",
                medical_class="Class 1",
                certificate_number="RCAA-MC-99211",
                valid_from=datetime.utcnow() - timedelta(days=180),
                valid_until=datetime.utcnow() + timedelta(days=185),
                clearance_status="cleared",
                vision_ok=True,
                hearing_ok=True,
                cardiovascular_ok=True,
                neurological_ok=True,
                respiratory_ok=True,
                musculoskeletal_ok=True,
                psychiatric_ok=True,
                notes="Excellent physiological indices. Confirmed fit for Category I flight operations under RCAA regulations.",
                created_by=john.id
            )
            db.add(rec)

    # 2. F/O Sarah UWASE (sarah@aeroguard.com) - Expiring Soon Class 1 (10 days from now)
    if "sarah@aeroguard.com" in aviators_map:
        sarah = aviators_map["sarah@aeroguard.com"]
        if not db.query(MedicalRecord).filter(MedicalRecord.user_id == sarah.id).first():
            rec = MedicalRecord(
                user_id=sarah.id,
                record_date=datetime.utcnow() - timedelta(days=355),
                examination_type="periodic",
                examining_physician="Dr. Jean HABIMANA",
                medical_facility="Akagera Aviation Health Center",
                medical_class="Class 1",
                certificate_number="RCAA-MC-44910",
                valid_from=datetime.utcnow() - timedelta(days=355),
                valid_until=datetime.utcnow() + timedelta(days=10),
                clearance_status="cleared",
                vision_ok=True,
                hearing_ok=True,
                cardiovascular_ok=True,
                neurological_ok=True,
                respiratory_ok=True,
                musculoskeletal_ok=True,
                psychiatric_ok=True,
                limitations="Must wear corrective lenses for distant vision.",
                conditions="Mild refractive error",
                notes="Renewal physical scheduled. Re-evaluation of visual acuity required. Operational eligibility valid with corrective lenses.",
                created_by=sarah.id
            )
            db.add(rec)

    # 3. Capt. David NKUSI (david@aeroguard.com) - Grounded / Suspended
    if "david@aeroguard.com" in aviators_map:
        david = aviators_map["david@aeroguard.com"]
        if not db.query(MedicalRecord).filter(MedicalRecord.user_id == david.id).first():
            rec = MedicalRecord(
                user_id=david.id,
                record_date=datetime.utcnow() - timedelta(days=240),
                examination_type="special",
                examining_physician="Dr. Jean HABIMANA",
                medical_facility="Akagera Aviation Health Center",
                medical_class="Class 1",
                certificate_number="RCAA-MC-11045",
                valid_from=datetime.utcnow() - timedelta(days=240),
                valid_until=datetime.utcnow() + timedelta(days=120),
                clearance_status="suspended",
                vision_ok=True,
                hearing_ok=True,
                cardiovascular_ok=False,  # BP failure
                neurological_ok=True,
                respiratory_ok=True,
                musculoskeletal_ok=True,
                psychiatric_ok=True,
                limitations="Temporarily grounded. Unfit for flight operations.",
                conditions="Grade 2 Hypertension, severe sleep debt fatigue",
                medications="Lisinopril 10mg daily",
                notes="Cardiovascular clinical screening flagged blood pressure of 165/102 mmHg. Severe fatigue-related indicators reported. Subject grounded until blood pressure stabilized and cardiologist clearance obtained.",
                created_by=david.id
            )
            db.add(rec)

    # 4. Capt. Alice UWIMANA (alice@aeroguard.com) - Active Class 1
    if "alice@aeroguard.com" in aviators_map:
        alice = aviators_map["alice@aeroguard.com"]
        if not db.query(MedicalRecord).filter(MedicalRecord.user_id == alice.id).first():
            rec = MedicalRecord(
                user_id=alice.id,
                record_date=datetime.utcnow() - timedelta(days=90),
                examination_type="annual",
                examining_physician="Dr. Jean HABIMANA",
                medical_facility="Akagera Aviation Health Center",
                medical_class="Class 1",
                certificate_number="RCAA-MC-88123",
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
                notes="Physical indices optimal. Fit for multi-pilot transport aircraft duty.",
                created_by=alice.id
            )
            db.add(rec)

    # 5. Capt. Emmanuel HABIMANA (emmanuel@aeroguard.com) - Expired
    if "emmanuel@aeroguard.com" in aviators_map:
        emmanuel = aviators_map["emmanuel@aeroguard.com"]
        if not db.query(MedicalRecord).filter(MedicalRecord.user_id == emmanuel.id).first():
            rec = MedicalRecord(
                user_id=emmanuel.id,
                record_date=datetime.utcnow() - timedelta(days=395),
                examination_type="annual",
                examining_physician="Dr. Jean HABIMANA",
                medical_facility="Akagera Aviation Health Center",
                medical_class="Class 1",
                certificate_number="RCAA-MC-33100",
                valid_from=datetime.utcnow() - timedelta(days=395),
                valid_until=datetime.utcnow() - timedelta(days=30),
                clearance_status="pending",  # shows expired state due to valid_until in the past
                vision_ok=True,
                hearing_ok=True,
                cardiovascular_ok=True,
                neurological_ok=True,
                respiratory_ok=True,
                musculoskeletal_ok=True,
                psychiatric_ok=True,
                limitations="Grounded due to certificate expiry.",
                notes="Annual Class 1 medical expired on calendar limits. Awaiting periodic renewal physical.",
                created_by=emmanuel.id
            )
            db.add(rec)

    db.commit()
    print(f"   [DONE] Created RCAA Medical Records")

db.close()
print("\n" + "=" * 50)
print("DATABASE SEEDING COMPLETE!")
print("   * Users: Login with Password123!")
print("   * Pilots: 10 crew members with varied risk levels")
print("   * Health, Alcohol, Duty, Fitness, Medical records seeded")
print("=" * 50)

