from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import FitnessAssessment, HealthRecord, AlcoholScreening, User, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL, SUBMIT_ASSESSMENT
from pydantic import BaseModel, Field

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class FitnessAssessmentCreate(BaseModel):
    user_id: int
    sleep_hours_last_night: float = Field(..., ge=0, le=24)
    sleep_quality_rating: float = Field(..., ge=1, le=10)
    stress_level: float = Field(..., ge=1, le=10)
    fatigue_level: float = Field(..., ge=1, le=10)
    workload_perception: float = Field(..., ge=1, le=10)
    duty_hours_today: float = Field(..., ge=0, le=24)
    physical_condition: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    illness_symptoms: Optional[str] = None
    medication_taken: Optional[str] = None
    feeling_ready: str = Field(..., pattern="^(yes|no|uncertain)$")
    flight_number: Optional[str] = None
    notes: Optional[str] = None

class SupervisorOverrideRequest(BaseModel):
    justification: str = Field(..., min_length=20, description="Must provide a detailed justification")

class FitnessAssessmentResponse(BaseModel):
    id: int
    user_id: int
    assessment_date: datetime
    overall_score: float
    health_score: Optional[float]
    fatigue_score: Optional[float]
    alcohol_substance_score: Optional[float]
    psychological_score: Optional[float]
    stress_score: Optional[float]
    risk_level: str
    alertness_level: str
    fit_for_duty: bool
    clearance_status: str
    clearance_level: str
    restrictions: Optional[str]
    assessed_by: Optional[str]
    valid_until: Optional[datetime]
    flight_number: Optional[str]
    supervisor_override: bool
    ai_confidence_score: Optional[float]
    notes: Optional[str]
    created_at: datetime

    # New fields
    sleep_hours_last_night: Optional[float]
    sleep_quality_rating: Optional[float]
    stress_level: Optional[float]
    fatigue_level: Optional[float]
    workload_perception: Optional[float]
    duty_hours_today: Optional[float]
    physical_condition: Optional[str]
    illness_symptoms: Optional[str]
    medication_taken: Optional[str]
    feeling_ready: Optional[str]
    response_anomaly_detected: bool
    anomaly_type: Optional[str]
    anomaly_description: Optional[str]
    manual_review_required: bool

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/fitness", response_model=FitnessAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_fitness_assessment(
    data: FitnessAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a fitness-for-duty assessment from manual inputs.
    Calculates fatigue score, readiness classification, and executes response consistency checks.
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    # ═══ FATIGUE SCORE CALCULATION ═══
    sleep_factor = max(0, 10 - data.sleep_hours_last_night) * 5  # 0-50
    stress_factor = data.stress_level * 4                        # 0-40
    fatigue_factor = data.fatigue_level * 3                      # 0-30
    duty_factor = min(data.duty_hours_today, 12) * 2             # 0-24

    base_fatigue = (sleep_factor + stress_factor + fatigue_factor + duty_factor) / 1.44
    calculated_fatigue_score = min(100, max(0, base_fatigue))

    # Map legacy scores for UI charts
    mapped_fatigue_score = 100 - calculated_fatigue_score
    mapped_stress_score = 100 - data.stress_level * 10
    mapped_psychological_score = 100 - data.workload_perception * 10
    mapped_health_score = 100.0 if data.physical_condition == "excellent" else (
        85.0 if data.physical_condition == "good" else (
            70.0 if data.physical_condition == "fair" else 50.0
        )
    )

    # Check latest alcohol screening
    latest_alcohol = (
        db.query(AlcoholScreening)
        .filter(
            AlcoholScreening.user_id == data.user_id,
            AlcoholScreening.screening_date >= datetime.utcnow() - timedelta(hours=12),
        )
        .order_by(desc(AlcoholScreening.screening_date))
        .first()
    )
    alcohol_score = 100.0
    if latest_alcohol and latest_alcohol.bac_level > 0.00:
        alcohol_score = 0.0  # Force grounding due to BAC breach

    # ═══ READINESS CLASSIFICATION ═══
    if calculated_fatigue_score < 30 and data.feeling_ready == "yes":
        classification = "Fit for Duty"
        readiness_score = 95
        risk_level = "LOW"
        clearance_status = "cleared"
        clearance_level = "green"
        restrictions = None
    elif calculated_fatigue_score < 50 and data.feeling_ready != "no":
        classification = "Fit for Duty"
        readiness_score = 80
        risk_level = "LOW"
        clearance_status = "cleared"
        clearance_level = "green"
        restrictions = None
    elif calculated_fatigue_score < 70:
        classification = "Limited Duty"
        readiness_score = 60
        risk_level = "MEDIUM"
        clearance_status = "conditional"
        clearance_level = "yellow"
        restrictions = '["Monitor fatigue during flight", "Maximum 6-hour duty period"]'
    else:
        classification = "Not Fit for Duty"
        readiness_score = 25
        risk_level = "HIGH"
        clearance_status = "grounded"
        clearance_level = "red"
        restrictions = '["GROUNDED - High fatigue risk", "Minimum 10-hour rest required"]'

    # Alcohol override
    if alcohol_score < 100.0:
        classification = "Not Fit for Duty"
        readiness_score = 10
        risk_level = "CRITICAL"
        clearance_status = "grounded"
        clearance_level = "red"
        restrictions = '["GROUNDED - Pre-flight alcohol test violation", "Mandatory supervisor review"]'

    # ═══ RESPONSE VALIDATION - DETECT INCONSISTENCIES ═══
    anomalies = []
    
    # Rule 1: Sleep < 5 hours but fatigue level is low
    if data.sleep_hours_last_night < 5 and data.fatigue_level <= 2:
        anomalies.append("sleep_fatigue_discrepancy")

    # Rule 2: Workload >= 8 but stress level is low
    if data.workload_perception >= 8 and data.stress_level <= 2:
        anomalies.append("workload_stress_discrepancy")

    # Rule 3: Duty hours > 12 but fatigue level is low
    if data.duty_hours_today > 12 and data.fatigue_level <= 2:
        anomalies.append("duty_fatigue_discrepancy")

    # Rule 4: Checked severe symptoms (sluggishness, micro-sleeps) but fatigue level is low
    symptoms_lower = (data.illness_symptoms or "").lower()
    if any(s in symptoms_lower for s in ["sluggishness", "micro-sleeps", "microsleep"]) and data.fatigue_level <= 2:
        anomalies.append("contradictory_symptoms")

    # Rule 5: Pattern copying anomaly (5 identical consecutive entries)
    recent = db.query(FitnessAssessment).filter(
        FitnessAssessment.user_id == data.user_id
    ).order_by(desc(FitnessAssessment.assessment_date)).limit(4).all()

    if len(recent) == 4:
        pattern_match = True
        for r in recent:
            if not (
                r.sleep_hours_last_night is not None and abs(r.sleep_hours_last_night - data.sleep_hours_last_night) < 0.1 and
                r.stress_level is not None and abs(r.stress_level - data.stress_level) < 0.1 and
                r.fatigue_level is not None and abs(r.fatigue_level - data.fatigue_level) < 0.1 and
                r.workload_perception is not None and abs(r.workload_perception - data.workload_perception) < 0.1
            ):
                pattern_match = False
                break
        if pattern_match:
            anomalies.append("pattern_copying_anomaly")

    anomaly_detected = len(anomalies) > 0
    anomaly_str = ", ".join(anomalies) if anomaly_detected else None
    anomaly_desc = f"Consistency check flagged: {anomaly_str}" if anomaly_detected else None
    review_required = anomaly_detected

    # If anomaly detected, force manual review and demote clearance if cleared
    if anomaly_detected and clearance_status == "cleared":
        clearance_status = "conditional"
        clearance_level = "yellow"
        classification = "Limited Duty"
        if not restrictions:
            restrictions = '["Flagged by Response Consistency AI", "Requires supervisor verification"]'

    assessment = FitnessAssessment(
        user_id=data.user_id,
        overall_score=readiness_score,
        health_score=mapped_health_score,
        fatigue_score=mapped_fatigue_score,
        alcohol_substance_score=alcohol_score,
        psychological_score=mapped_psychological_score,
        stress_score=mapped_stress_score,
        risk_level=risk_level,
        alertness_level="high" if mapped_fatigue_score >= 80 else ("moderate" if mapped_fatigue_score >= 60 else "low"),
        fit_for_duty=(clearance_status != "grounded"),
        clearance_status=clearance_status,
        clearance_level=clearance_level,
        restrictions=restrictions,
        assessed_by="AeroGuard AI Consistency Engine",
        valid_until=datetime.utcnow() + timedelta(hours=12),
        flight_number=data.flight_number,
        ai_confidence_score=98.5,
        notes=data.notes,
        
        # New manual declaration fields
        sleep_hours_last_night=data.sleep_hours_last_night,
        sleep_quality_rating=data.sleep_quality_rating,
        stress_level=data.stress_level,
        fatigue_level=data.fatigue_level,
        workload_perception=data.workload_perception,
        duty_hours_today=data.duty_hours_today,
        physical_condition=data.physical_condition,
        illness_symptoms=data.illness_symptoms,
        medication_taken=data.medication_taken,
        feeling_ready=data.feeling_ready,
        
        # Anomaly flags
        response_anomaly_detected=anomaly_detected,
        anomaly_type=anomaly_str,
        anomaly_description=anomaly_desc,
        manual_review_required=review_required,
        similar_past_responses=4 if "pattern_copying_anomaly" in anomalies else 0
    )

    db.add(assessment)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="readiness_assessment_submitted",
        resource_type="readiness_assessment",
        resource_id=str(data.user_id),
        action_details=f"Readiness check -> {clearance_status.upper()} | Score: {readiness_score} | Flags: {anomaly_str or 'NONE'}",
        module="Operational Readiness",
        success=True,
    ))
    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/{assessment_id}/override")
def supervisor_override(
    assessment_id: int,
    override_data: SupervisorOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supervisor override on a CONDITIONAL assessment.
    Cannot override alcohol/substance violations.
    """
    from auth.permissions import require_supervisor_or_above
    from models import UserRole
    if current_user.role not in [UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER, UserRole.ADMINISTRATOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor role required.")

    assessment = db.query(FitnessAssessment).filter(FitnessAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    if assessment.alcohol_substance_score is not None and assessment.alcohol_substance_score < 100:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot override: alcohol/substance violation detected.",
        )
    if assessment.clearance_status == "grounded" and assessment.clearance_level == "red":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot override a critical grounding. Medical clearance required.",
        )

    assessment.supervisor_override = True
    assessment.override_by = current_user.id
    assessment.override_justification = override_data.justification
    assessment.override_timestamp = datetime.utcnow()
    assessment.clearance_status = "conditional"
    assessment.fit_for_duty = True

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="supervisor_override",
        resource_type="fitness_assessment",
        resource_id=str(assessment_id),
        action_details=f"Override by {current_user.full_name}: {override_data.justification}",
        module="Operational Readiness",
        success=True,
    ))
    db.commit()
    return {"message": "Override applied successfully", "assessment_id": assessment_id}


@router.get("/latest/{user_id}", response_model=FitnessAssessmentResponse)
def get_latest_assessment(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent fitness assessment for a user."""
    assessment = (
        db.query(FitnessAssessment)
        .filter(FitnessAssessment.user_id == user_id)
        .order_by(desc(FitnessAssessment.assessment_date))
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessments found.")
    return assessment


@router.get("/history", response_model=List[FitnessAssessmentResponse])
def get_assessment_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(30, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fitness assessment history."""
    can_view_all = has_permission(current_user, VIEW_CREW_DATA)
    query = db.query(FitnessAssessment)

    if user_id:
        if not can_view_all and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        query = query.filter(FitnessAssessment.user_id == user_id)
    elif not can_view_all:
        query = query.filter(FitnessAssessment.user_id == current_user.id)

    return query.order_by(desc(FitnessAssessment.assessment_date)).limit(limit).all()


@router.get("/dashboard-stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Summary stats for the dashboard: cleared/conditional/grounded counts."""
    if not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Get latest assessment per user (last 24 hours)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent = (
        db.query(FitnessAssessment)
        .filter(FitnessAssessment.assessment_date >= cutoff)
        .all()
    )

    cleared = sum(1 for a in recent if a.clearance_status == "cleared")
    conditional = sum(1 for a in recent if a.clearance_status == "conditional")
    grounded = sum(1 for a in recent if a.clearance_status == "grounded")

    return {
        "total_assessments_24h": len(recent),
        "cleared": cleared,
        "conditional": conditional,
        "grounded": grounded,
        "compliance_rate": round((cleared / len(recent) * 100) if recent else 100.0, 1),
    }
