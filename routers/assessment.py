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

    # Scores
    health_score: Optional[float] = Field(None, ge=0, le=100)
    fatigue_score: Optional[float] = Field(None, ge=0, le=100)
    alcohol_substance_score: Optional[float] = Field(None, ge=0, le=100)
    psychological_score: Optional[float] = Field(None, ge=0, le=100)
    stress_score: Optional[float] = Field(None, ge=0, le=100)

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

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS — AI scoring logic
# ──────────────────────────────────────────────

def _calculate_overall_score(
    health: Optional[float],
    fatigue: Optional[float],
    alcohol: Optional[float],
    psych: Optional[float],
    stress: Optional[float],
) -> float:
    """Weighted scoring: alcohol/substance has highest weight."""
    weights = {
        "health": 0.20,
        "fatigue": 0.25,
        "alcohol": 0.30,
        "psych": 0.15,
        "stress": 0.10,
    }
    scores = {
        "health": health or 75.0,
        "fatigue": fatigue or 75.0,
        "alcohol": alcohol or 100.0,
        "psych": psych or 80.0,
        "stress": stress or 80.0,
    }
    total = sum(scores[k] * weights[k] for k in weights)
    return round(total, 1)

def _classify_assessment(overall: float, alcohol_score: Optional[float]) -> dict:
    """Classify risk, alertness, clearance based on score and alcohol override."""
    # Alcohol override — if any alcohol detected (score < 100), ground immediately
    if alcohol_score is not None and alcohol_score < 100:
        return {
            "risk_level": "CRITICAL",
            "alertness_level": "critical",
            "fit_for_duty": False,
            "clearance_status": "grounded",
            "clearance_level": "red",
            "restrictions": '["GROUNDED - Alcohol/substance violation", "Mandatory counseling required"]',
        }

    if overall >= 85:
        return {
            "risk_level": "LOW",
            "alertness_level": "high",
            "fit_for_duty": True,
            "clearance_status": "cleared",
            "clearance_level": "green",
            "restrictions": None,
        }
    elif overall >= 70:
        return {
            "risk_level": "MEDIUM",
            "alertness_level": "moderate",
            "fit_for_duty": True,
            "clearance_status": "conditional",
            "clearance_level": "yellow",
            "restrictions": '["Monitor fatigue during flight", "Maximum 6-hour duty period"]',
        }
    elif overall >= 50:
        return {
            "risk_level": "HIGH",
            "alertness_level": "low",
            "fit_for_duty": False,
            "clearance_status": "grounded",
            "clearance_level": "red",
            "restrictions": '["GROUNDED - High fatigue risk", "Minimum 10-hour rest required"]',
        }
    else:
        return {
            "risk_level": "CRITICAL",
            "alertness_level": "critical",
            "fit_for_duty": False,
            "clearance_status": "grounded",
            "clearance_level": "red",
            "restrictions": '["GROUNDED - Critical risk level", "Medical evaluation required before return"]',
        }

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
    Create a fitness-for-duty assessment.
    Automatically calculates overall score, risk level, and clearance status.
    BAC override: any alcohol detected = immediate GROUNDED.
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    # Check latest alcohol screening — auto-override if grounded
    latest_alcohol = (
        db.query(AlcoholScreening)
        .filter(
            AlcoholScreening.user_id == data.user_id,
            AlcoholScreening.screening_date >= datetime.utcnow() - timedelta(hours=12),
        )
        .order_by(desc(AlcoholScreening.screening_date))
        .first()
    )

    alcohol_score = data.alcohol_substance_score
    if latest_alcohol and latest_alcohol.bac_level > 0.00:
        alcohol_score = 0.0  # Force grounding

    overall = _calculate_overall_score(
        data.health_score, data.fatigue_score, alcohol_score,
        data.psychological_score, data.stress_score
    )
    classification = _classify_assessment(overall, alcohol_score)

    assessment = FitnessAssessment(
        user_id=data.user_id,
        overall_score=overall,
        health_score=data.health_score,
        fatigue_score=data.fatigue_score,
        alcohol_substance_score=alcohol_score,
        psychological_score=data.psychological_score,
        stress_score=data.stress_score,
        risk_level=classification["risk_level"],
        alertness_level=classification["alertness_level"],
        fit_for_duty=classification["fit_for_duty"],
        clearance_status=classification["clearance_status"],
        clearance_level=classification["clearance_level"],
        restrictions=classification["restrictions"],
        assessed_by=current_user.full_name,
        valid_until=datetime.utcnow() + timedelta(hours=12),
        flight_number=data.flight_number,
        ai_confidence_score=92.0,
        notes=data.notes,
    )

    db.add(assessment)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="fitness_assessment_created",
        resource_type="fitness_assessment",
        resource_id=str(data.user_id),
        action_details=f"Fitness assessment → {classification['clearance_status'].upper()} | Score: {overall}",
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
