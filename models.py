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
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan", foreign_keys="[HealthRecord.user_id]")
    alcohol_screenings = relationship("AlcoholScreening", back_populates="user", cascade="all, delete-orphan", foreign_keys="[AlcoholScreening.user_id]")
    duty_periods = relationship("DutyPeriod", back_populates="user", cascade="all, delete-orphan", foreign_keys="[DutyPeriod.user_id]")
    fitness_assessments = relationship("FitnessAssessment", back_populates="user", cascade="all, delete-orphan", foreign_keys="[FitnessAssessment.user_id]")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan", foreign_keys="[AuditLog.user_id]")

# ============================================================================
# PILOT MODEL (legacy — kept for backward compat)
# ============================================================================

class Pilot(Base):
    __tablename__ = "pilots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    employee_id = Column(String, unique=True, nullable=False)
    role = Column(String, default="pilot")  # pilot, co-pilot, crew
    sleep_hours = Column(Float)
    duty_hours = Column(Float)
    stress_level = Column(Float)
    reaction_score = Column(Float)
    alertness_score = Column(Float)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)

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