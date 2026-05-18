"""
AeroGuard AI — Comprehensive Demo Seed Script v2.0
Seeds all tables including new modules: medical records, alertness,
FRMS, compliance, safety incidents, risk predictions, IoT devices.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Base, User, UserRole, HealthRecord, AlcoholScreening, SubstanceScreening
from models import DutyPeriod, FitnessAssessment, Notification, AuditLog, IoTDevice
from models import MedicalRecord, AlertnessReading, FRMSEntry, ComplianceCheck, SafetyIncident, RiskPredictionLog
from auth.utils import hash_password
from datetime import datetime, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def days_ago(n, hour=8): return datetime.utcnow() - timedelta(days=n, hours=hour)
def hours_ago(n):        return datetime.utcnow() - timedelta(hours=n)
def days_ahead(n):       return datetime.utcnow() + timedelta(days=n)

print("[*] Seeding AeroGuard AI database...")

# ── 1. USERS ─────────────────────────────────────────────────────────────────
users_data = [
    {"email": "admin@aeroguard.rw",    "full_name": "Kagabo Emmanuel",    "employee_id": "AG-ADMIN-001", "role": UserRole.ADMINISTRATOR,   "license": None},
    {"email": "safety@aeroguard.rw",   "full_name": "Uwimana Diane",      "employee_id": "AG-SAF-001",   "role": UserRole.SAFETY_OFFICER,  "license": None},
    {"email": "medical@aeroguard.rw",  "full_name": "Nkurunziza Jean",    "employee_id": "AG-MED-001",   "role": UserRole.MEDICAL_OFFICER, "license": None},
    {"email": "supervisor@aeroguard.rw","full_name": "Habimana Claude",   "employee_id": "AG-SUP-001",   "role": UserRole.SUPERVISOR,      "license": None},
    {"email": "pilot1@aeroguard.rw",   "full_name": "Nzabonimpa Eric",    "employee_id": "AG-PIL-001",   "role": UserRole.AVIATOR,         "license": "RCAA-CPL-RW-2021-0045"},
    {"email": "pilot2@aeroguard.rw",   "full_name": "Mukamana Grace",     "employee_id": "AG-PIL-002",   "role": UserRole.AVIATOR,         "license": "RCAA-CPL-RW-2020-0031"},
    {"email": "pilot3@aeroguard.rw",   "full_name": "Bizimana Patrick",   "employee_id": "AG-PIL-003",   "role": UserRole.AVIATOR,         "license": "RCAA-CPL-RW-2022-0067"},
]

created_users = {}
for u in users_data:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if not existing:
        user = User(
            email=u["email"], full_name=u["full_name"], employee_id=u["employee_id"],
            role=u["role"], password_hash=hash_password("AeroGuard2025!"),
            license_number=u.get("license"), is_active=True,
            last_login=hours_ago(random.randint(1, 48)),
        )
        db.add(user)
        db.flush()
        created_users[u["employee_id"]] = user
    else:
        created_users[u["employee_id"]] = existing

db.commit()
aviators = [created_users["AG-PIL-001"], created_users["AG-PIL-002"], created_users["AG-PIL-003"]]
admin    = created_users["AG-ADMIN-001"]
medical  = created_users["AG-MED-001"]
safety   = created_users["AG-SAF-001"]
print(f"  [+] {len(users_data)} users seeded")

# ── 2. IoT DEVICES ────────────────────────────────────────────────────────────
iot_devices = [
    {"name": "Garmin Pilot Watch #1",   "type": "Smartwatch",      "device_id": "IOT-SW-001", "battery": 87},
    {"name": "Garmin Pilot Watch #2",   "type": "Smartwatch",      "device_id": "IOT-SW-002", "battery": 64},
    {"name": "Neurosity EEG Headset #1","type": "EEG Headset",     "device_id": "IOT-EEG-001","battery": 72},
    {"name": "Nonin Pulse Oximeter #1", "type": "Pulse Oximeter",  "device_id": "IOT-SPO-001","battery": 91},
    {"name": "Draeger Breathalyzer #1",  "type": "Breathalyzer",    "device_id": "IOT-BAC-001","battery": 100},
    {"name": "Tobii Eye Tracker #1",    "type": "Eye Tracker",     "device_id": "IOT-EYE-001","battery": 55},
]
for d in iot_devices:
    if not db.query(IoTDevice).filter(IoTDevice.device_id == d["device_id"]).first():
        db.add(IoTDevice(name=d["name"], type=d["type"], device_id=d["device_id"],
                         battery=d["battery"], status="active"))
db.commit()
print(f"  [+] {len(iot_devices)} IoT devices seeded")

# ── 3. HEALTH RECORDS (7 days per aviator) ───────────────────────────────────
for pilot in aviators:
    for day in range(7, 0, -1):
        db.add(HealthRecord(
            user_id=pilot.id,
            record_date=days_ago(day),
            heart_rate=random.uniform(62, 88),
            blood_pressure_systolic=random.uniform(110, 130),
            blood_pressure_diastolic=random.uniform(70, 85),
            oxygen_saturation=random.uniform(96, 100),
            sleep_hours=random.uniform(5.5, 8.5),
            sleep_quality=random.uniform(55, 95),
            stress_level=random.uniform(2, 7),
            fatigue_score=random.uniform(20, 70),
            alertness_score=random.uniform(55, 95),
            reaction_time_ms=random.uniform(220, 380),
            cognitive_score=random.uniform(65, 95),
            notes="Auto-seeded health record",
            created_by=medical.id,
        ))
db.commit()
print("  [+] Health records seeded (7 days x 3 pilots)")

# ── 4. ALCOHOL SCREENINGS ────────────────────────────────────────────────────
for pilot in aviators:
    for day in range(5, 0, -1):
        db.add(AlcoholScreening(
            user_id=pilot.id, screening_date=days_ago(day),
            screening_type="pre_flight", bac_level=0.00,
            test_method="breathalyzer", device_id="IOT-BAC-001",
            result_status="cleared", is_violation=False,
            witness_name="Supervisor Habimana", supervised_by=created_users["AG-SUP-001"].id,
            test_location="KGL Pre-flight Bay A",
        ))
# One violation for demo
db.add(AlcoholScreening(
    user_id=aviators[2].id, screening_date=days_ago(10),
    screening_type="random", bac_level=0.03,
    test_method="breathalyzer", result_status="grounded",
    is_violation=True, violation_details="BAC 0.03% detected during random check",
    supervised_by=created_users["AG-SUP-001"].id,
))
db.commit()
print("  [+] Alcohol screenings seeded")

# ── 5. SUBSTANCE SCREENINGS ───────────────────────────────────────────────────
for pilot in aviators:
    db.add(SubstanceScreening(
        user_id=pilot.id, screening_date=days_ago(random.randint(5, 25)),
        screening_type="scheduled", cannabis_result="negative",
        opioids_result="negative", cocaine_result="negative",
        amphetamines_result="negative", benzodiazepines_result="negative",
        test_method="urine", result_status="cleared", is_violation=False,
        laboratory_id="RURA-LAB-KGL-01",
        report_number=f"SUBST-{random.randint(1000,9999)}",
    ))
db.commit()
print("  [+] Substance screenings seeded")

# ── 6. MEDICAL RECORDS ────────────────────────────────────────────────────────
medical_classes = ["Class 1", "Class 1", "Class 2"]
for i, pilot in enumerate(aviators):
    db.add(MedicalRecord(
        user_id=pilot.id,
        record_date=days_ago(random.randint(30, 180)),
        examination_type="annual",
        examining_physician=f"Dr. {['Munyakazi R.','Gasana P.','Uwase C.'][i]}",
        medical_facility="King Faisal Hospital Kigali",
        medical_class=medical_classes[i],
        certificate_number=f"RCAA-MED-{pilot.employee_id}-2025",
        valid_from=days_ago(180),
        valid_until=days_ahead(185),
        clearance_status="cleared",
        vision_ok=True, hearing_ok=True, cardiovascular_ok=True,
        neurological_ok=True, respiratory_ok=True,
        musculoskeletal_ok=True, psychiatric_ok=True,
        limitations=None, conditions=None, medications=None,
        notes="Annual medical examination -- all parameters within ICAO limits.",
        created_by=medical.id, is_confidential=True,
    ))
db.commit()
print("  [+] Medical records seeded")

# ── 7. ALERTNESS READINGS (5 days x 3 readings/day per pilot) ────────────────
for pilot in aviators:
    for day in range(5, 0, -1):
        for reading_num in range(3):
            score = random.uniform(45, 95)
            level = "high" if score >= 80 else "moderate" if score >= 60 else "low" if score >= 40 else "critical"
            db.add(AlertnessReading(
                user_id=pilot.id,
                reading_timestamp=days_ago(day) + timedelta(hours=reading_num * 4),
                source=random.choice(["iot_smartwatch", "iot_eeg_headset", "manual"]),
                alertness_score=score,
                fatigue_index=100 - score + random.uniform(-5, 5),
                reaction_time_ms=random.uniform(220, 380),
                heart_rate=random.uniform(62, 88),
                hrv_score=random.uniform(30, 80),
                cognitive_load=random.uniform(30, 75),
                attention_score=random.uniform(50, 95),
                alertness_level=level,
                risk_flag=(score < 60),
                device_id=random.choice(["IOT-SW-001", "IOT-EEG-001"]),
            ))
db.commit()
print("  [+] Alertness readings seeded")

# ── 8. FRMS ENTRIES (7 days per pilot) ───────────────────────────────────────
statuses = ["normal", "normal", "watch", "warning", "normal", "normal", "normal"]
for pilot in aviators:
    cumulative = 0.0
    for day in range(7, 0, -1):
        cumulative = min(100, cumulative + random.uniform(3, 12))
        frms_s = statuses[7 - day]
        db.add(FRMSEntry(
            user_id=pilot.id, entry_date=days_ago(day),
            entry_type="daily_log",
            cumulative_fatigue_score=round(cumulative, 1),
            sleep_debt_hours=random.uniform(0, 4),
            circadian_phase=random.choice(["normal", "normal", "delayed"]),
            wake_hours=random.uniform(4, 16),
            duty_hours_7d=random.uniform(20, 50),
            duty_hours_28d=random.uniform(60, 150),
            night_duties_7d=random.randint(0, 2),
            predicted_fatigue_level="LOW" if cumulative < 40 else "MEDIUM" if cumulative < 60 else "HIGH",
            biomathematical_score=random.uniform(30, 80),
            alertness_window="06:00-14:00",
            frms_status=frms_s,
            intervention_required=(frms_s in ["warning", "critical"]),
            logged_by=created_users["AG-SUP-001"].id,
        ))
db.commit()
print("  [+] FRMS entries seeded")

# ── 9. FITNESS ASSESSMENTS ────────────────────────────────────────────────────
clearances = ["cleared", "cleared", "conditional"]
for i, pilot in enumerate(aviators):
    for day in range(3, 0, -1):
        clr = clearances[i]
        db.add(FitnessAssessment(
            user_id=pilot.id, assessment_date=days_ago(day),
            overall_score=random.uniform(72, 95),
            health_score=random.uniform(70, 98), fatigue_score=random.uniform(65, 95),
            alcohol_substance_score=100.0, psychological_score=random.uniform(70, 95),
            stress_score=random.uniform(65, 90),
            risk_level="LOW" if clr == "cleared" else "MEDIUM",
            alertness_level="high" if clr == "cleared" else "moderate",
            fit_for_duty=(clr != "grounded"), clearance_status=clr,
            clearance_level="green" if clr == "cleared" else "yellow",
            assessed_by=medical.full_name,
            valid_until=days_ahead(1), ai_confidence_score=92.0,
        ))
db.commit()
print("  [+] Fitness assessments seeded")

# ── 10. DUTY PERIODS ─────────────────────────────────────────────────────────
routes = [("KGL","UGA"), ("KGL","BUR"), ("KGL","DRC")]
aircraft = ["Cessna C208", "DHC-6 Twin Otter", "Bombardier Q400"]
for i, pilot in enumerate(aviators):
    for day in range(5, 1, -1):
        start = days_ago(day)
        end   = start + timedelta(hours=random.uniform(3, 7))
        db.add(DutyPeriod(
            user_id=pilot.id, duty_start=start, duty_end=end,
            duty_type="flight", status="completed",
            flight_number=f"RWA{random.randint(100,999)}",
            aircraft_type=aircraft[i],
            route=f"{routes[i][0]}-{routes[i][1]}",
            departure_airport=routes[i][0], arrival_airport=routes[i][1],
            duty_hours=round((end - start).total_seconds() / 3600, 2),
            flight_hours=round((end - start).total_seconds() / 3600 - 0.5, 2),
            alcohol_screening_completed=True, alcohol_screening_passed=True,
            substance_screening_completed=True, substance_screening_passed=True,
            fitness_assessment_completed=True, fitness_assessment_passed=True,
        ))
db.commit()
print("  [+] Duty periods seeded")

# ── 11. RISK PREDICTIONS ──────────────────────────────────────────────────────
for pilot in aviators:
    for day in range(5, 0, -1):
        score = random.uniform(15, 65)
        level = "LOW" if score < 25 else "MEDIUM" if score < 50 else "HIGH" if score < 75 else "CRITICAL"
        db.add(RiskPredictionLog(
            user_id=pilot.id,
            prediction_timestamp=days_ago(day),
            sleep_hours_input=random.uniform(5, 8),
            duty_hours_input=random.uniform(2, 10),
            stress_level_input=random.uniform(2, 7),
            alertness_score_input=random.uniform(55, 90),
            predicted_risk_level=level,
            risk_score=round(score, 1),
            confidence_score=random.uniform(82, 96),
            model_version="v1.0",
            contributing_factors=str(["sleep_debt"] if score > 50 else []),
            recommendations="Maintain rest schedule." if level == "LOW" else "Monitor fatigue levels.",
            alert_generated=(level in ["HIGH", "CRITICAL"]),
            action_taken="none",
        ))
db.commit()
print("  [+] Risk predictions seeded")

# ── 12. COMPLIANCE CHECKS ─────────────────────────────────────────────────────
check_types = ["alcohol_policy", "duty_hours", "rcaa_medical"]
refs = {
    "alcohol_policy": "RCAA-OPS-CAR-AIR-014 § 4.2",
    "duty_hours":     "RCAA-OPS-FTL-2023 § 3.1",
    "rcaa_medical":   "RCAA-MED-001 § 2.1",
}
for pilot in aviators:
    for ct in check_types:
        db.add(ComplianceCheck(
            user_id=pilot.id, check_type=ct,
            regulation_reference=refs[ct],
            is_compliant=True, compliance_score=100.0,
            violations_found=0, status="resolved",
            checked_by=safety.id,
        ))
# One violation
db.add(ComplianceCheck(
    user_id=aviators[2].id, check_type="alcohol_policy",
    regulation_reference=refs["alcohol_policy"],
    is_compliant=False, compliance_score=0.0,
    violations_found=1,
    violation_details='["BAC 0.03% detected - pre_flight screening violation on ' + str(days_ago(10).date()) + '"]',
    status="resolved",
    resolution_notes="Pilot grounded 72h. Counseling completed. Cleared to return.",
    resolved_by=safety.id, resolved_at=days_ago(7),
    checked_by=safety.id,
))
db.commit()
print("  [+] Compliance checks seeded")

# ── 13. SAFETY INCIDENTS ──────────────────────────────────────────────────────
incidents = [
    {"title": "Pre-flight fatigue indicator flagged", "type": "fatigue",      "severity": "medium", "days": 12},
    {"title": "BAC violation -- random screening",     "type": "alcohol",      "severity": "high",   "days": 10},
    {"title": "Near-miss during approach to BUR",     "type": "near_miss",    "severity": "critical","days": 20},
    {"title": "Equipment fault -- EEG sensor dropout", "type": "equipment",    "severity": "low",    "days": 5},
]
statuses_inc = ["closed", "closed", "under_investigation", "closed"]
for i, inc in enumerate(incidents):
    db.add(SafetyIncident(
        reporter_id=safety.id,
        involved_user_id=aviators[i % 3].id,
        incident_date=days_ago(inc["days"]),
        incident_type=inc["type"], severity=inc["severity"],
        title=inc["title"],
        description=f"Incident report: {inc['title']}. Logged during operational monitoring by Safety Officer.",
        location="KJIA -- Kigali International Airport",
        flight_number=f"RWA{400+i}",
        status=statuses_inc[i],
        rcaa_reported=(inc["severity"] in ["high", "critical"]),
        root_cause="Operational fatigue accumulation" if inc["type"] == "fatigue" else None,
        corrective_action="Rest period enforced. FRMS review conducted." if statuses_inc[i] == "closed" else None,
    ))
db.commit()
print("  [+] Safety incidents seeded")

# ── 14. NOTIFICATIONS ─────────────────────────────────────────────────────────
notif_data = [
    (admin.id,   "System Startup Complete",         "AeroGuard AI v2.0 is now fully operational.", "info",    "low"),
    (safety.id,  "FRMS Alert -- Pilot Bizimana", "Cumulative fatigue score elevated. Review recommended.", "warning", "high"),
    (aviators[0].id, "Pre-flight Clearance",     "You are cleared for duty. Valid for 12 hours.", "info", "low"),
    (aviators[1].id, "Low Alertness Detected",  "Alertness score 42/100 -- classified LOW. Rest required.", "alert", "critical"),
    (created_users["AG-SUP-001"].id, "Pending Assessment Override", "1 conditional assessment awaiting supervisor review.", "warning", "medium"),
]
for uid, title, msg, ntype, priority in notif_data:
    db.add(Notification(user_id=uid, title=title, message=msg,
                        notification_type=ntype, priority=priority,
                        status="unread", action_required=(priority in ["high","critical"])))
db.commit()
print("  [+] Notifications seeded")

# ── 15. AUDIT LOGS ────────────────────────────────────────────────────────────
audit_events = [
    (admin.id,   "user_login",          "user",        str(admin.id),    "Administrator login", "Authentication"),
    (safety.id,  "compliance_check_run","compliance",  "fleet",          "Fleet compliance check run", "Compliance"),
    (medical.id, "medical_record_created","medical_record", str(aviators[0].id), "Annual medical -- Class 1 cleared", "Medical Records"),
    (created_users["AG-SUP-001"].id, "duty_started", "duty_period", str(aviators[0].id), "Flight duty started RWA501", "Flight Duty"),
    (aviators[0].id, "alertness_reading_submitted", "alertness_reading", str(aviators[0].id), "Score: 82 | Level: high", "Alertness & Fatigue"),
]
for uid, action, rtype, rid, details, module in audit_events:
    db.add(AuditLog(user_id=uid, action_type=action, resource_type=rtype,
                    resource_id=rid, action_details=details, module=module,
                    ip_address="192.168.1.1", success=True))
db.commit()
print("  [+] Audit logs seeded")

print("\nAll tables seeded successfully!")
print("\nDemo Login Credentials (password: AeroGuard2025!):")
print("  Administrator  : admin@aeroguard.rw")
print("  Safety Officer : safety@aeroguard.rw")
print("  Medical Officer: medical@aeroguard.rw")
print("  Supervisor     : supervisor@aeroguard.rw")
print("  Pilot 1        : pilot1@aeroguard.rw")
print("  Pilot 2        : pilot2@aeroguard.rw")
print("  Pilot 3        : pilot3@aeroguard.rw")
print("\nAPI Docs: http://localhost:8000/docs")

db.close()
