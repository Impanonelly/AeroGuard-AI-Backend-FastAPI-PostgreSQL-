from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import FitnessAssessment, HealthRecord, AlcoholScreening, User, AuditLog, MedicalRecord, Notification
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
    consecutive_work_days: Optional[int] = 1
    medical_decision: Optional[str] = None

    # Apple Watch Telemetry
    apple_watch_sleep_hours: Optional[float] = None
    apple_watch_sleep_quality: Optional[float] = None
    apple_watch_resting_hr: Optional[float] = None
    apple_watch_current_hr: Optional[float] = None
    apple_watch_activity_level: Optional[float] = None

    # Pre-Flight Self Assessment
    self_alertness_level: Optional[float] = None
    alcohol_declared: Optional[bool] = False

    # Reaction Time Assessment
    reaction_time_ms: Optional[float] = None

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

    # Apple Watch & Redesign Telemetry
    apple_watch_sleep_hours: Optional[float] = None
    apple_watch_sleep_quality: Optional[float] = None
    apple_watch_resting_hr: Optional[float] = None
    apple_watch_current_hr: Optional[float] = None
    apple_watch_activity_level: Optional[float] = None
    self_alertness_level: Optional[float] = None
    alcohol_declared: bool
    reaction_time_ms: Optional[float] = None
    consecutive_work_days: Optional[int] = None

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
    Create an aviation operational readiness assessment from manual inputs, Apple Watch telemetry, and reaction time.
    Calculates fatigue score (0-100), readiness score (0-100), risk levels, and clearance status.
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    # 1. Fetch latest health record and medical certificate status
    latest_health = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == data.user_id)
        .order_by(desc(HealthRecord.record_date))
        .first()
    )
    heart_rate = latest_health.heart_rate if (latest_health and latest_health.heart_rate) else 72.0
    bp_sys = latest_health.blood_pressure_systolic if (latest_health and latest_health.blood_pressure_systolic) else 120.0
    bp_dia = latest_health.blood_pressure_diastolic if (latest_health and latest_health.blood_pressure_diastolic) else 80.0

    latest_medical = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.user_id == data.user_id)
        .order_by(desc(MedicalRecord.record_date))
        .first()
    )
    
    medical_ok = True
    medical_details = "Valid ICAO Medical Certificate"
    if latest_medical:
        if latest_medical.clearance_status != "cleared":
            medical_ok = False
            medical_details = f"Restricted/Suspended Medical Certificate ({latest_medical.clearance_status})"
        elif latest_medical.valid_until and latest_medical.valid_until < datetime.utcnow():
            medical_ok = False
            medical_details = f"Expired Medical Certificate (expired on {latest_medical.valid_until.strftime('%Y-%m-%d')})"
    else:
        medical_ok = False
        medical_details = "No Medical Record registered in database"

    # 2. Check latest alcohol screening (last 12h)
    latest_alcohol = (
        db.query(AlcoholScreening)
        .filter(
            AlcoholScreening.user_id == data.user_id,
            AlcoholScreening.screening_date >= datetime.utcnow() - timedelta(hours=12),
        )
        .order_by(desc(AlcoholScreening.screening_date))
        .first()
    )
    has_alcohol_violation = (latest_alcohol and latest_alcohol.bac_level > 0.00) or data.alcohol_declared

    # 3. Calculate Fatigue Score (0-100) (higher is worse)
    sleep_hrs = data.apple_watch_sleep_hours if data.apple_watch_sleep_hours is not None else data.sleep_hours_last_night
    sleep_quality = data.apple_watch_sleep_quality if data.apple_watch_sleep_quality is not None else (data.sleep_quality_rating * 10.0)

    sleep_penalty = max(0.0, 8.0 - sleep_hrs) * 12.5
    quality_penalty = max(0.0, 80.0 - sleep_quality) * 0.5
    self_fatigue_penalty = data.fatigue_level * 3.0
    duty_penalty = max(0.0, data.duty_hours_today - 8.0) * 4.0

    # Heart Rate elevation penalty
    hr_penalty = 0.0
    watch_rhr = data.apple_watch_resting_hr if data.apple_watch_resting_hr is not None else (latest_health.resting_heart_rate if latest_health else 65.0)
    watch_cur_hr = data.apple_watch_current_hr if data.apple_watch_current_hr is not None else heart_rate
    if watch_rhr and watch_cur_hr:
        hr_diff = watch_cur_hr - watch_rhr
        if hr_diff > 15.0:
            hr_penalty = min(15.0, (hr_diff - 15.0) * 1.0)

    # Reaction Time penalty
    rt_penalty = 0.0
    if data.reaction_time_ms is not None:
        if data.reaction_time_ms > 280.0:
            rt_penalty = min(25.0, (data.reaction_time_ms - 280.0) * 0.15)
        elif data.reaction_time_ms < 150.0:
            rt_penalty = 5.0  # Suspiciously fast click

    calculated_fatigue_score = min(100.0, max(0.0, sleep_penalty + quality_penalty + self_fatigue_penalty + duty_penalty + hr_penalty + rt_penalty))

    # 4. Calculate Readiness Score (0-100) (higher is better)
    base_readiness = 100.0
    fatigue_deduction = calculated_fatigue_score * 0.5
    stress_deduction = data.stress_level * 2.5
    alertness_rating = data.self_alertness_level if data.self_alertness_level is not None else (10.0 - data.fatigue_level)
    alertness_deduction = max(0.0, 10.0 - alertness_rating) * 2.5

    calculated_readiness_score = min(100.0, max(0.0, base_readiness - (fatigue_deduction + stress_deduction + alertness_deduction)))

    # Force 0 readiness on critical violations
    if has_alcohol_violation or not medical_ok:
        calculated_readiness_score = 0.0

    # 5. Determine Operational Clearance and Risk Levels
    restrictions_list = []
    medical_decision = getattr(data, 'medical_decision', None)
    if medical_decision:
        if medical_decision in ["Fit for Duty", "cleared"]:
            classification = "Fit for Duty"
            risk_level = "LOW"
            clearance_status = "cleared"
            clearance_level = "green"
        elif medical_decision in ["Monitoring Required", "conditional"]:
            classification = "Limited Duty"
            risk_level = "MEDIUM"
            clearance_status = "conditional"
            clearance_level = "yellow"
            restrictions_list.extend(["Maximum 6-hour duty period", "No night operations", "Monitor fatigue during flight"])
        elif medical_decision in ["Restricted", "restricted"]:
            classification = "Not Fit for Duty"
            risk_level = "HIGH"
            clearance_status = "restricted"
            clearance_level = "orange"
            restrictions_list.append("RESTRICTED - Threshold exceeded. Medical review required.")
        elif medical_decision in ["Grounded", "grounded"]:
            classification = "Not Fit for Duty"
            risk_level = "CRITICAL"
            clearance_status = "grounded"
            clearance_level = "red"
            restrictions_list.append("GROUNDED - Critical fatigue risk detected. Flight operations prohibited.")
        else:
            classification = "Fit for Duty"
            risk_level = "LOW"
            clearance_status = "cleared"
            clearance_level = "green"
    else:
        if not medical_ok:
            classification = "Not Fit for Duty"
            risk_level = "CRITICAL"
            clearance_status = "grounded"
            clearance_level = "red"
            restrictions_list.append(f"GROUNDED - {medical_details}")
        elif has_alcohol_violation:
            classification = "Not Fit for Duty"
            risk_level = "CRITICAL"
            clearance_status = "grounded"
            clearance_level = "red"
            restrictions_list.append("GROUNDED - Pre-flight alcohol declaration or test violation")
        elif calculated_fatigue_score > 65.0 or calculated_readiness_score < 50.0:
            classification = "Not Fit for Duty"
            risk_level = "HIGH"
            clearance_status = "grounded"
            clearance_level = "red"
            restrictions_list.append("GROUNDED - High fatigue index / low readiness score. Minimum 10h rest required.")
        elif calculated_fatigue_score > 35.0 or calculated_readiness_score < 80.0:
            classification = "Limited Duty"
            risk_level = "MEDIUM"
            clearance_status = "conditional"
            clearance_level = "yellow"
            restrictions_list.extend(["Maximum 6-hour duty period", "No night operations", "Monitor fatigue during flight"])
        else:
            classification = "Fit for Duty"
            risk_level = "LOW"
            clearance_status = "cleared"
            clearance_level = "green"

    # Map legacy score outputs for UI charts compatibility
    mapped_health_score = 100.0 if data.physical_condition == "excellent" else (
        85.0 if data.physical_condition == "good" else (
            70.0 if data.physical_condition == "fair" else 50.0
        )
    )
    mapped_stress_score = 100.0 - (data.stress_level * 10.0)
    mapped_psychological_score = 100.0 - (data.workload_perception * 10.0)

    # 6. Response Validation Anomalies
    anomalies = []
    if data.sleep_hours_last_night < 5 and data.fatigue_level <= 2:
        anomalies.append("sleep_fatigue_discrepancy")
    if data.workload_perception >= 8 and data.stress_level <= 2:
        anomalies.append("workload_stress_discrepancy")
    if data.duty_hours_today > 12 and data.fatigue_level <= 2:
        anomalies.append("duty_fatigue_discrepancy")

    symptoms_lower = (data.illness_symptoms or "").lower()
    if any(s in symptoms_lower for s in ["sluggishness", "micro-sleeps", "microsleep"]) and data.fatigue_level <= 2:
        anomalies.append("contradictory_symptoms")

    # Pattern copying anomaly (5 identical consecutive entries)
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

    if bp_sys > 140 or bp_sys < 90 or bp_dia > 90 or bp_dia < 60:
        anomalies.append("abnormal_blood_pressure_alert")

    anomaly_detected = len(anomalies) > 0
    anomaly_str = ", ".join(anomalies) if anomaly_detected else None
    anomaly_desc = f"Consistency check flagged: {anomaly_str}" if anomaly_detected else None
    review_required = anomaly_detected

    if anomaly_detected and clearance_status == "cleared":
        clearance_status = "conditional"
        clearance_level = "yellow"
        classification = "Limited Duty"
        restrictions_list.append("Flagged by Response Consistency AI (requires supervisor override)")

    import json
    restrictions_json = json.dumps(restrictions_list) if restrictions_list else None

    # Instantiate DB model instance
    assessment = FitnessAssessment(
        user_id=data.user_id,
        overall_score=calculated_readiness_score,
        health_score=mapped_health_score,
        fatigue_score=calculated_fatigue_score,
        alcohol_substance_score=0.0 if has_alcohol_violation else 100.0,
        psychological_score=mapped_psychological_score,
        stress_score=mapped_stress_score,
        risk_level=risk_level,
        alertness_level="high" if calculated_readiness_score >= 80 else ("moderate" if calculated_readiness_score >= 50 else "low"),
        fit_for_duty=(clearance_status != "grounded"),
        clearance_status=clearance_status,
        clearance_level=clearance_level,
        restrictions=restrictions_json,
        assessed_by=current_user.full_name if current_user.role == "medical_officer" else "AeroGuard AI Readiness Engine",
        valid_until=datetime.utcnow() + timedelta(hours=12),
        flight_number=data.flight_number,
        ai_confidence_score=99.2,
        notes=data.notes,
        consecutive_work_days=data.consecutive_work_days,
        
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
        
        # New telemetry
        apple_watch_sleep_hours=data.apple_watch_sleep_hours,
        apple_watch_sleep_quality=data.apple_watch_sleep_quality,
        apple_watch_resting_hr=data.apple_watch_resting_hr,
        apple_watch_current_hr=data.apple_watch_current_hr,
        apple_watch_activity_level=data.apple_watch_activity_level,
        self_alertness_level=data.self_alertness_level,
        alcohol_declared=data.alcohol_declared,
        reaction_time_ms=data.reaction_time_ms,
        
        # Anomalies
        response_anomaly_detected=anomaly_detected,
        anomaly_type=anomaly_str,
        anomaly_description=anomaly_desc,
        manual_review_required=review_required,
        similar_past_responses=4 if "pattern_copying_anomaly" in anomalies else 0
    )

    db.add(assessment)
    
    # Auto-generate notification for grounded / restricted fatigue alerts
    if clearance_status in ["grounded", "restricted"]:
        db.add(Notification(
            user_id=data.user_id,
            title=f"⚠️ Fatigue Alert - {classification.upper()}",
            message=f"Crew member flagged as '{clearance_status.upper()}' by Medical Officer {current_user.full_name}. Reason: {data.notes or 'Fatigue review required.'}",
            notification_type="alert",
            priority="critical" if clearance_status == "grounded" else "high",
            action_required=True,
        ))
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="readiness_assessment_submitted",
        resource_type="readiness_assessment",
        resource_id=str(data.user_id),
        action_details=f"Readiness check -> {clearance_status.upper()} | Score: {calculated_readiness_score} | Flags: {anomaly_str or 'NONE'}",
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


@router.get("/{assessment_id}/certificate", response_class=Response)
def get_readiness_certificate(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and download an official RCAA Operational Readiness Certificate
    with a verification QR code for a cleared assessment.
    """
    from services.pdf_generator import generate_readiness_certificate

    assessment = db.query(FitnessAssessment).filter(FitnessAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment record not found.")

    # Only the pilot themselves, or a supervisor/admin/safety officer can access the certificate
    if current_user.id != assessment.user_id and not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Generating certificate is only valid for cleared (or conditionally cleared) status
    if assessment.clearance_status not in ["cleared", "conditional"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate certificate for a grounded pilot (Clearance: {assessment.clearance_status.upper()})."
        )

    verify_url = f"http://localhost:3000/verify/{assessment_id}"
    pdf_content = generate_readiness_certificate(assessment, verify_url)

    # Log to audit trail
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="readiness_certificate_downloaded",
        resource_type="readiness_assessment",
        resource_id=str(assessment_id),
        action_details=f"Readiness certificate downloaded for user {assessment.user_id}",
        module="Operational Readiness",
        success=True,
    ))
    db.commit()

    filename = f"AeroGuard_Clearance_Certificate_{assessment_id}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/verify/{assessment_id}")
def verify_assessment_public(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to verify the operational readiness status of a pilot's certificate.
    This does not expose private sensitive medical metrics, only duty clearance status.
    """
    assessment = db.query(FitnessAssessment).filter(FitnessAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Readiness certificate record not found.")

    pilot = assessment.user
    if not pilot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated crew member not found.")

    # Check if certificate is expired (validity period has passed)
    is_expired = False
    if assessment.valid_until and datetime.utcnow() > assessment.valid_until:
        is_expired = True

    return {
        "certificate_id": assessment.id,
        "pilot_name": pilot.full_name,
        "employee_id": pilot.employee_id,
        "role": pilot.role,
        "flight_number": assessment.flight_number,
        "clearance_status": "expired" if is_expired else assessment.clearance_status,
        "clearance_level": "gray" if is_expired else assessment.clearance_level,
        "assessment_date": assessment.assessment_date,
        "valid_until": assessment.valid_until,
        "is_expired": is_expired,
        "verification_timestamp": datetime.utcnow()
    }
