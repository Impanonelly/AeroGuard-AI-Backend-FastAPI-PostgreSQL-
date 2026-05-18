from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

# ============================================================================
# ENUMS
# ============================================================================

class UserRole:
    AVIATOR = "aviator"
    SUPERVISOR = "supervisor"
    SAFETY_OFFICER = "safety_officer"
    MEDICAL_OFFICER = "medical_officer"
    ADMINISTRATOR = "administrator"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ClearanceStatus(str, enum.Enum):
    CLEARED = "cleared"
    CONDITIONAL = "conditional"
    GROUNDED = "grounded"

class ScreeningType(str, enum.Enum):
    PRE_FLIGHT = "pre_flight"
    POST_FLIGHT = "post_flight"
    RANDOM = "random"
    SCHEDULED = "scheduled"

class DutyStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    employee_id = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False, default=UserRole.AVIATOR)
    license_number = Column(String, nullable=True)
    certification_details = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    session_timeout = Column(Integer, default=900)  # 15 minutes in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    security_keys = relationship("UserSecurityKey", back_populates="user", cascade="all, delete-orphan")
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan", foreign_keys="HealthRecord.user_id")
    alcohol_screenings = relationship("AlcoholScreening", back_populates="user", cascade="all, delete-orphan", foreign_keys="AlcoholScreening.user_id")
    substance_screenings = relationship("SubstanceScreening", back_populates="user", cascade="all, delete-orphan", foreign_keys="SubstanceScreening.user_id")
    duty_periods = relationship("DutyPeriod", back_populates="user", cascade="all, delete-orphan", foreign_keys="DutyPeriod.user_id")
    fitness_assessments = relationship("FitnessAssessment", back_populates="user", cascade="all, delete-orphan", foreign_keys="FitnessAssessment.user_id")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan", foreign_keys="AuditLog.user_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", foreign_keys="Notification.user_id")
    medical_records = relationship("MedicalRecord", back_populates="user", cascade="all, delete-orphan", foreign_keys="MedicalRecord.user_id")
    alertness_readings = relationship("AlertnessReading", back_populates="user", cascade="all, delete-orphan", foreign_keys="AlertnessReading.user_id")
    frms_entries = relationship("FRMSEntry", back_populates="user", cascade="all, delete-orphan", foreign_keys="FRMSEntry.user_id")
    risk_predictions = relationship("RiskPredictionLog", back_populates="user", cascade="all, delete-orphan", foreign_keys="RiskPredictionLog.user_id")

class UserSecurityKey(Base):
    __tablename__ = "user_security_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_id = Column(String, unique=True, index=True, nullable=False)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0)
    device_type = Column(String, nullable=True) # e.g., "Windows Hello", "TouchID"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="security_keys")

# ============================================================================
# HEALTH RECORD MODEL
# ============================================================================

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Vitals
    record_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    heart_rate = Column(Float, nullable=True)              # bpm
    blood_pressure_systolic = Column(Float, nullable=True) # mmHg
    blood_pressure_diastolic = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)             # Celsius
    oxygen_saturation = Column(Float, nullable=True)       # %
    respiratory_rate = Column(Float, nullable=True)        # breaths/min

    # Sleep
    sleep_hours = Column(Float, nullable=True)             # hours
    sleep_quality = Column(Float, nullable=True)           # 0-100

    # Fatigue / Stress
    stress_level = Column(Float, nullable=True)            # 0-10
    fatigue_score = Column(Float, nullable=True)           # 0-100
    alertness_score = Column(Float, nullable=True)         # 0-100
    reaction_time_ms = Column(Float, nullable=True)        # milliseconds

    # Cognitive
    cognitive_score = Column(Float, nullable=True)         # 0-100
    memory_score = Column(Float, nullable=True)
    attention_score = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="health_records", foreign_keys=[user_id])

# ============================================================================
# ALCOHOL SCREENING MODEL
# ============================================================================

class AlcoholScreening(Base):
    __tablename__ = "alcohol_screenings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    screening_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    screening_type = Column(String, default="pre_flight")  # pre_flight, post_flight, random
    bac_level = Column(Float, nullable=False)              # Blood Alcohol Content %
    test_method = Column(String, default="breathalyzer")   # breathalyzer, blood, urine
    device_id = Column(String, nullable=True)

    # Result
    result_status = Column(String, nullable=False)         # cleared, warning, grounded
    is_violation = Column(Boolean, default=False)
    violation_details = Column(Text, nullable=True)

    # Supervision
    witness_name = Column(String, nullable=True)
    supervised_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    test_location = Column(String, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alcohol_screenings", foreign_keys=[user_id])

# ============================================================================
# SUBSTANCE SCREENING MODEL
# ============================================================================

class SubstanceScreening(Base):
    __tablename__ = "substance_screenings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    screening_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    screening_type = Column(String, default="random")  # pre_flight, random, scheduled
    
    # Categories (JSON string for simplicity or boolean fields)
    cannabis_result = Column(String, default="negative")   # negative, positive, trace
    opioids_result = Column(String, default="negative")
    cocaine_result = Column(String, default="negative")
    amphetamines_result = Column(String, default="negative")  # negative, trace, positive
    benzodiazepines_result = Column(String, default="negative") # negative, trace, positive
    test_method = Column(String, default="urine")        # urine, saliva, hair
    laboratory_id = Column(String, nullable=True)
    report_number = Column(String, nullable=True)

    # Result
    result_status = Column(String, nullable=False)         # cleared, flagged, pending
    is_violation = Column(Boolean, default=False)
    violation_details = Column(Text, nullable=True)

    # Supervision
    supervised_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="substance_screenings", foreign_keys=[user_id])

# ============================================================================
# DUTY PERIOD MODEL
# ============================================================================

class DutyPeriod(Base):
    __tablename__ = "duty_periods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    duty_start = Column(DateTime, nullable=False)
    duty_end = Column(DateTime, nullable=True)
    duty_type = Column(String, default="flight")           # flight, standby, training, ground
    status = Column(String, default="scheduled")           # scheduled, active, completed, cancelled

    # Flight info
    flight_number = Column(String, nullable=True)
    aircraft_type = Column(String, nullable=True)
    route = Column(String, nullable=True)
    departure_airport = Column(String, nullable=True)
    arrival_airport = Column(String, nullable=True)

    # Computed hours
    duty_hours = Column(Float, nullable=True)
    flight_hours = Column(Float, nullable=True)
    rest_hours_before = Column(Float, nullable=True)

    # Screening gates
    alcohol_screening_completed = Column(Boolean, default=False)
    alcohol_screening_passed = Column(Boolean, default=False)
    substance_screening_completed = Column(Boolean, default=False)
    substance_screening_passed = Column(Boolean, default=False)
    fitness_assessment_completed = Column(Boolean, default=False)
    fitness_assessment_passed = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="duty_periods", foreign_keys=[user_id])

# ============================================================================
# FITNESS ASSESSMENT MODEL
# ============================================================================

class FitnessAssessment(Base):
    __tablename__ = "fitness_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    assessment_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite scores (0-100)
    overall_score = Column(Float, nullable=False)
    health_score = Column(Float, nullable=True)
    fatigue_score = Column(Float, nullable=True)
    alcohol_substance_score = Column(Float, nullable=True)
    psychological_score = Column(Float, nullable=True)
    stress_score = Column(Float, nullable=True)

    # Risk classification
    risk_level = Column(String, default="LOW")             # LOW, MEDIUM, HIGH, CRITICAL
    alertness_level = Column(String, default="high")       # high, moderate, low, critical

    # Clearance
    fit_for_duty = Column(Boolean, default=False)
    clearance_status = Column(String, default="grounded")  # cleared, conditional, grounded
    clearance_level = Column(String, default="red")        # green, yellow, red
    restrictions = Column(Text, nullable=True)             # JSON array as string

    # Assessment metadata
    assessed_by = Column(String, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    flight_number = Column(String, nullable=True)

    # Supervisor override
    supervisor_override = Column(Boolean, default=False)
    override_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    override_justification = Column(Text, nullable=True)
    override_timestamp = Column(DateTime, nullable=True)

    # AI
    ai_confidence_score = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="fitness_assessments", foreign_keys=[user_id])

# ============================================================================
# PILOT MODEL
# ============================================================================

class Pilot(Base):
    __tablename__ = "pilots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    employee_id = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False) # e.g. "Captain", "First Officer"
    
    # Live Status Metrics
    sleep_hours = Column(Float, default=0.0)
    duty_hours = Column(Float, default=0.0)
    stress_level = Column(Float, default=0.0)
    reaction_score = Column(Float, default=0.0)
    alertness_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW") # LOW, MEDIUM, HIGH
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# AI MODEL TRACKING
# ============================================================================

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="online") # online, offline, training
    accuracy = Column(Float, default=0.0)
    last_sync = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# IOT DEVICE TRACKING
# ============================================================================

class IoTDevice(Base):
    __tablename__ = "iot_devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # Smartwatch, EEG Headset, etc.
    status = Column(String, default="active") # active, inactive, charging
    battery = Column(Integer, default=100)
    last_sync = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String, unique=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action_type = Column(String, nullable=False)           # login, logout, assessment, etc.
    resource_type = Column(String, nullable=True)          # user, pilot, assessment, etc.
    resource_id = Column(String, nullable=True)
    action_details = Column(Text, nullable=True)
    module = Column(String, nullable=True)

    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])

# ============================================================================
# NOTIFICATION MODEL
# ============================================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)     # alert, info, warning, critical
    priority = Column(String, default="medium")            # low, medium, high, critical
    status = Column(String, default="unread")              # unread, read, acknowledged

    action_required = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])

# ============================================================================
# MEDICAL RECORD MODEL
# ============================================================================

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    record_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    examination_type = Column(String, default="annual")      # annual, periodic, special, return_to_duty
    examining_physician = Column(String, nullable=True)
    medical_facility = Column(String, nullable=True)

    # Medical clearance
    medical_class = Column(String, nullable=True)            # Class 1, Class 2, Class 3 (ICAO)
    certificate_number = Column(String, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    clearance_status = Column(String, default="pending")     # cleared, restricted, suspended, pending

    # Clinical findings
    vision_ok = Column(Boolean, default=True)
    hearing_ok = Column(Boolean, default=True)
    cardiovascular_ok = Column(Boolean, default=True)
    neurological_ok = Column(Boolean, default=True)
    respiratory_ok = Column(Boolean, default=True)
    musculoskeletal_ok = Column(Boolean, default=True)
    psychiatric_ok = Column(Boolean, default=True)

    # Restrictions / conditions
    limitations = Column(Text, nullable=True)                # e.g., "Must wear corrective lenses"
    conditions = Column(Text, nullable=True)                 # Active diagnosed conditions
    medications = Column(Text, nullable=True)                # Current medications

    # Confidentiality
    is_confidential = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="medical_records", foreign_keys=[user_id])

# ============================================================================
# ALERTNESS READING MODEL
# ============================================================================

class AlertnessReading(Base):
    __tablename__ = "alertness_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    reading_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String, default="manual")                # manual, iot_smartwatch, iot_eeg, iot_camera

    # Alertness metrics
    alertness_score = Column(Float, nullable=False)          # 0-100
    fatigue_index = Column(Float, nullable=True)             # 0-100 (higher = more fatigued)
    reaction_time_ms = Column(Float, nullable=True)          # milliseconds
    blink_rate = Column(Float, nullable=True)                # blinks per minute
    eye_closure_duration = Column(Float, nullable=True)      # PERCLOS % (% time eyes >80% closed)

    # Cognitive
    cognitive_load = Column(Float, nullable=True)            # 0-100
    attention_score = Column(Float, nullable=True)           # 0-100

    # Physiological from IoT
    heart_rate = Column(Float, nullable=True)                # bpm
    hrv_score = Column(Float, nullable=True)                 # Heart Rate Variability
    eeg_theta_power = Column(Float, nullable=True)           # EEG theta band (fatigue marker)
    eeg_alpha_power = Column(Float, nullable=True)           # EEG alpha band

    # Classification
    alertness_level = Column(String, default="moderate")     # high, moderate, low, critical
    risk_flag = Column(Boolean, default=False)               # True if unsafe to fly

    # Device
    device_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alertness_readings", foreign_keys=[user_id])

# ============================================================================
# FRMS ENTRY MODEL (Fatigue Risk Management System)
# ============================================================================

class FRMSEntry(Base):
    __tablename__ = "frms_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    entry_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    entry_type = Column(String, default="daily_log")         # daily_log, incident, alert, intervention

    # FRMS Metrics
    cumulative_fatigue_score = Column(Float, nullable=True)  # 0-100 rolling fatigue
    sleep_debt_hours = Column(Float, nullable=True)          # Accumulated sleep debt
    circadian_phase = Column(String, nullable=True)          # normal, delayed, advanced, disrupted
    wake_hours = Column(Float, nullable=True)                # Hours since last sleep
    duty_hours_7d = Column(Float, nullable=True)             # Total duty hours in last 7 days
    duty_hours_28d = Column(Float, nullable=True)            # Total duty hours in last 28 days
    night_duties_7d = Column(Integer, nullable=True)         # Night duties in last 7 days

    # Bio-mathematical model outputs
    predicted_fatigue_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    biomathematical_score = Column(Float, nullable=True)     # SAFE model / FAID score
    alertness_window = Column(String, nullable=True)         # Predicted alertness window

    # FRMS Status
    frms_status = Column(String, default="normal")           # normal, watch, warning, critical
    intervention_required = Column(Boolean, default=False)
    intervention_type = Column(String, nullable=True)        # rest, reduced_duty, grounded, counseling

    notes = Column(Text, nullable=True)
    logged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="frms_entries", foreign_keys=[user_id])

# ============================================================================
# COMPLIANCE CHECK MODEL
# ============================================================================

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # None = fleet-wide check

    check_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    check_type = Column(String, nullable=False)              # rcaa_medical, duty_hours, alcohol_policy, substance_policy, frms
    regulation_reference = Column(String, nullable=True)    # e.g., "RCAA-OPS-1.2.3"
    description = Column(Text, nullable=True)

    # Result
    is_compliant = Column(Boolean, nullable=False, default=True)
    compliance_score = Column(Float, nullable=True)          # 0-100
    violations_found = Column(Integer, default=0)
    violation_details = Column(Text, nullable=True)          # JSON array as string

    # Resolution
    status = Column(String, default="open")                  # open, under_review, resolved, escalated
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# SAFETY INCIDENT MODEL
# ============================================================================

class SafetyIncident(Base):
    __tablename__ = "safety_incidents"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    involved_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    incident_date = Column(DateTime, nullable=False, index=True)
    report_date = Column(DateTime, default=datetime.utcnow)
    incident_type = Column(String, nullable=False)           # fatigue, alcohol, medical, operational, near_miss, equipment
    severity = Column(String, default="low")                 # low, medium, high, critical
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Location / Flight info
    location = Column(String, nullable=True)
    flight_number = Column(String, nullable=True)
    aircraft_type = Column(String, nullable=True)
    phase_of_flight = Column(String, nullable=True)          # taxi, takeoff, cruise, approach, landing

    # Investigation
    status = Column(String, default="reported")              # reported, under_investigation, closed, escalated
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    investigated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # RCAA reporting
    rcaa_reported = Column(Boolean, default=False)
    rcaa_reference = Column(String, nullable=True)

    is_confidential = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# RISK PREDICTION LOG MODEL
# ============================================================================

class RiskPredictionLog(Base):
    __tablename__ = "risk_prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    prediction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Input features used for prediction
    sleep_hours_input = Column(Float, nullable=True)
    duty_hours_input = Column(Float, nullable=True)
    stress_level_input = Column(Float, nullable=True)
    alertness_score_input = Column(Float, nullable=True)
    heart_rate_input = Column(Float, nullable=True)
    reaction_time_input = Column(Float, nullable=True)

    # AI Output
    predicted_risk_level = Column(String, nullable=False)    # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, nullable=False)               # 0-100
    confidence_score = Column(Float, nullable=True)          # 0-100 AI confidence
    model_version = Column(String, default="v1.0")

    # Contributing factors (JSON string)
    contributing_factors = Column(Text, nullable=True)       # e.g. ["sleep_debt", "high_stress"]
    recommendations = Column(Text, nullable=True)            # AI-generated recommendations

    # Action taken
    alert_generated = Column(Boolean, default=False)
    action_taken = Column(String, nullable=True)             # none, notified_supervisor, grounded

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="risk_predictions", foreign_keys=[user_id])