from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import DutyPeriod, AlcoholScreening, FitnessAssessment, User, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, SUBMIT_ASSESSMENT
from pydantic import BaseModel, Field

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class DutyStartRequest(BaseModel):
    user_id: int
    duty_type: str = Field(default="flight", description="flight | standby | training | ground")
    flight_number: Optional[str] = None
    aircraft_type: Optional[str] = None
    route: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    notes: Optional[str] = None

class DutyEndRequest(BaseModel):
    duty_id: int
    flight_hours: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class DutyResponse(BaseModel):
    id: int
    user_id: int
    duty_start: datetime
    duty_end: Optional[datetime]
    duty_type: str
    status: str
    flight_number: Optional[str]
    aircraft_type: Optional[str]
    route: Optional[str]
    departure_airport: Optional[str]
    arrival_airport: Optional[str]
    duty_hours: Optional[float]
    flight_hours: Optional[float]
    alcohol_screening_completed: bool
    alcohol_screening_passed: bool
    substance_screening_completed: bool
    substance_screening_passed: bool
    fitness_assessment_completed: bool
    fitness_assessment_passed: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _check_alcohol_clearance(user_id: int, db: Session) -> bool:
    """Latest pre-flight screening must be 'cleared' (within last 12 hours)."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=12)
    screening = (
        db.query(AlcoholScreening)
        .filter(
            AlcoholScreening.user_id == user_id,
            AlcoholScreening.screening_type == "pre_flight",
            AlcoholScreening.screening_date >= cutoff,
            AlcoholScreening.result_status == "cleared",
        )
        .order_by(desc(AlcoholScreening.screening_date))
        .first()
    )
    return screening is not None

def _check_fitness_clearance(user_id: int, db: Session) -> bool:
    """Latest fitness assessment must be 'cleared'."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=12)
    assessment = (
        db.query(FitnessAssessment)
        .filter(
            FitnessAssessment.user_id == user_id,
            FitnessAssessment.assessment_date >= cutoff,
            FitnessAssessment.clearance_status == "cleared",
        )
        .order_by(desc(FitnessAssessment.assessment_date))
        .first()
    )
    return assessment is not None

def _check_substance_clearance(user_id: int, db: Session) -> bool:
    """Latest substance screening must be 'cleared' (not flagged)."""
    from models import SubstanceScreening
    screening = (
        db.query(SubstanceScreening)
        .filter(SubstanceScreening.user_id == user_id)
        .order_by(desc(SubstanceScreening.screening_date))
        .first()
    )
    # Unlike alcohol, substance screenings might be less frequent (e.g. monthly)
    # But for flight duty, we ensure the status is 'cleared'
    if not screening:
        return False
    return screening.result_status == "cleared"

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/start", response_model=DutyResponse, status_code=status.HTTP_201_CREATED)
def start_duty(
    data: DutyStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a duty period.
    Gates:
    1. No current active duty for user.
    2. Pre-flight alcohol screening passed (within 12 h).
    3. Fitness assessment cleared (within 12 h) — for flight duties.
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    # Check for already-active duty
    existing = (
        db.query(DutyPeriod)
        .filter(DutyPeriod.user_id == data.user_id, DutyPeriod.status == "active")
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has an active duty period (ID {existing.id}). End it first.",
        )

    # Check alcohol clearance
    alcohol_ok = _check_alcohol_clearance(data.user_id, db)
    fitness_ok = _check_fitness_clearance(data.user_id, db)
    substance_ok = _check_substance_clearance(data.user_id, db)

    if data.duty_type == "flight":
        if not alcohol_ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot start flight duty: No valid pre-flight alcohol screening (cleared, within 12 hours).",
            )
        if not substance_ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot start flight duty: Substance status is not CLEARED. Laboratory confirmation or screening required.",
            )
        if not fitness_ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot start flight duty: No valid fitness assessment (cleared, within 12 hours).",
            )

    duty = DutyPeriod(
        user_id=data.user_id,
        duty_start=datetime.utcnow(),
        duty_type=data.duty_type,
        status="active",
        flight_number=data.flight_number,
        aircraft_type=data.aircraft_type,
        route=data.route,
        departure_airport=data.departure_airport,
        arrival_airport=data.arrival_airport,
        alcohol_screening_completed=alcohol_ok,
        alcohol_screening_passed=alcohol_ok,
        substance_screening_completed=substance_ok,
        substance_screening_passed=substance_ok,
        fitness_assessment_completed=fitness_ok,
        fitness_assessment_passed=fitness_ok,
        notes=data.notes,
    )

    db.add(duty)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="duty_started",
        resource_type="duty_period",
        resource_id=str(data.user_id),
        action_details=f"Duty started: {data.duty_type} | Flight: {data.flight_number}",
        module="Duty Management",
        success=True,
    ))
    db.commit()
    db.refresh(duty)
    return duty


@router.post("/end", response_model=DutyResponse)
def end_duty(
    data: DutyEndRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End an active duty period. Calculates duty hours."""
    duty = db.query(DutyPeriod).filter(DutyPeriod.id == data.duty_id).first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty period not found.")
    if duty.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duty is not currently active.")

    now = datetime.utcnow()
    duty.duty_end = now
    duty.status = "completed"
    duty.flight_hours = data.flight_hours
    duty.duty_hours = round((now - duty.duty_start).total_seconds() / 3600, 2)
    if data.notes:
        duty.notes = data.notes

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="duty_ended",
        resource_type="duty_period",
        resource_id=str(duty.id),
        action_details=f"Duty completed: {duty.duty_hours}h total duty | {data.flight_hours}h flight",
        module="Duty Management",
        success=True,
    ))
    db.commit()
    db.refresh(duty)
    return duty


@router.get("/current/{user_id}", response_model=Optional[DutyResponse])
def get_current_duty(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current active duty for a user."""
    duty = (
        db.query(DutyPeriod)
        .filter(DutyPeriod.user_id == user_id, DutyPeriod.status == "active")
        .first()
    )
    return duty


@router.get("/history", response_model=List[DutyResponse])
def get_duty_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(30, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get duty period history."""
    can_view_all = has_permission(current_user, VIEW_CREW_DATA)
    query = db.query(DutyPeriod)

    if user_id:
        if not can_view_all and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        query = query.filter(DutyPeriod.user_id == user_id)
    elif not can_view_all:
        query = query.filter(DutyPeriod.user_id == current_user.id)

    return query.order_by(desc(DutyPeriod.duty_start)).limit(limit).all()
