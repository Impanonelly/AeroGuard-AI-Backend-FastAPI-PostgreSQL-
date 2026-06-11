from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import ReadinessAssessment, User, AuditLog, AlcoholScreening, HealthRecord
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, SUBMIT_ASSESSMENT

router = APIRouter()

class ReadinessAssessmentCreate(BaseModel):
    sleep_hours_last_night: float = Field(..., ge=0, le=24)
    sleep_quality_rating: float = Field(..., ge=1, le=10)
    stress_level: float = Field(..., ge=1, le=10)
    fatigue_level: float = Field(..., ge=1, le=10)
    workload_perception: float = Field(..., ge=1, le=10)
    duty_hours_today: float = Field(..., ge=0, le=24)
    physical_condition: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    feeling_ready: str = Field(..., pattern="^(yes|no|uncertain)$")

@router.post("/submit", tags=["readiness-assessment"])
def submit_readiness_assessment(
    assessment: ReadinessAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_assessment = ReadinessAssessment(
        user_id=current_user.id,
        sleep_hours_last_night=assessment.sleep_hours_last_night,
        sleep_quality_rating=assessment.sleep_quality_rating,
        stress_level=assessment.stress_level,
        fatigue_level=assessment.fatigue_level,
        workload_perception=assessment.workload_perception,
        duty_hours_today=assessment.duty_hours_today,
        physical_condition=assessment.physical_condition,
        feeling_ready=assessment.feeling_ready,
    )
    validate_and_score_assessment(db_assessment, current_user, db)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@router.get("/history/{user_id}", tags=["readiness-assessment"])
def get_readiness_history(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id and not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    assessments = db.query(ReadinessAssessment).filter(
        ReadinessAssessment.user_id == user_id,
        ReadinessAssessment.assessment_date >= cutoff_date
    ).order_by(desc(ReadinessAssessment.assessment_date)).all()
    return {"assessments": assessments, "total_count": len(assessments)}

def validate_and_score_assessment(assessment: ReadinessAssessment, user: User, db: Session):
    # Fetch latest health record to get heart rate and blood pressure
    latest_health = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(desc(HealthRecord.record_date))
        .first()
    )
    heart_rate = latest_health.heart_rate if (latest_health and latest_health.heart_rate) else 72.0
    bp_sys = latest_health.blood_pressure_systolic if (latest_health and latest_health.blood_pressure_systolic) else 120.0
    bp_dia = latest_health.blood_pressure_diastolic if (latest_health and latest_health.blood_pressure_diastolic) else 80.0

    sleep_factor = max(0, 10 - assessment.sleep_hours_last_night) * 5
    stress_factor = assessment.stress_level * 4
    fatigue_factor = assessment.fatigue_level * 3
    duty_factor = min(assessment.duty_hours_today, 12) * 2
    hr_factor = max(0, heart_rate - 70) * 0.4
    
    base_fatigue = (sleep_factor + stress_factor + fatigue_factor + duty_factor + hr_factor) / 1.44
    assessment.fatigue_score = min(100, max(0, base_fatigue))

    # Check latest alcohol screening in last 12 hours
    latest_alcohol = (
        db.query(AlcoholScreening)
        .filter(
            AlcoholScreening.user_id == user.id,
            AlcoholScreening.screening_date >= datetime.utcnow() - timedelta(hours=12),
        )
        .order_by(desc(AlcoholScreening.screening_date))
        .first()
    )
    has_alcohol_violation = latest_alcohol and latest_alcohol.bac_level > 0.00

    # ═══ CLASSIFICATION ═══
    if has_alcohol_violation:
        assessment.readiness_classification = "Not Fit for Duty"
        assessment.overall_readiness_score = 0.0
        assessment.risk_level = "CRITICAL"
        assessment.clearance_status = "grounded"
    elif assessment.fatigue_score <= 30.0:
        assessment.readiness_classification = "Fit for Duty"
        assessment.overall_readiness_score = 90.0 - (assessment.fatigue_score * 0.5)
        assessment.risk_level = "LOW"
        assessment.clearance_status = "cleared"
    elif assessment.fatigue_score <= 60.0:
        assessment.readiness_classification = "Monitor / Limited Duty"
        assessment.overall_readiness_score = 70.0 - ((assessment.fatigue_score - 30.0) * 0.6)
        assessment.risk_level = "MEDIUM"
        assessment.clearance_status = "conditional"
    else:
        assessment.readiness_classification = "Not Fit for Duty"
        assessment.overall_readiness_score = 20.0
        assessment.risk_level = "HIGH"
        assessment.clearance_status = "grounded"

    anomalies = []
    if assessment.sleep_hours_last_night < 4 and assessment.fatigue_level < 3:
        anomalies.append("sleep_debt_low_fatigue_mismatch")
    if assessment.duty_hours_today > 12 and assessment.feeling_ready == "yes":
        anomalies.append("high_duty_feeling_ready")
    if assessment.stress_level > 7 and assessment.workload_perception > 8 and assessment.feeling_ready == "yes":
        anomalies.append("stress_workload_ready_mismatch")

    # Abnormal blood pressure requires medical review
    is_bp_abnormal = bp_sys > 140 or bp_sys < 90 or bp_dia > 90 or bp_dia < 60
    if is_bp_abnormal:
        anomalies.append("abnormal_blood_pressure_alert")

    if anomalies:
        assessment.response_anomaly_detected = True
        assessment.anomaly_type = ", ".join(anomalies)
        assessment.manual_review_required = True
