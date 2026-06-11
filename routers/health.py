from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import HealthRecord, User, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL, SUBMIT_ASSESSMENT
from pydantic import BaseModel, Field

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class HealthRecordCreate(BaseModel):
    user_id: int

    # Vitals
    heart_rate: Optional[float] = Field(None, ge=30, le=250)
    resting_heart_rate: Optional[float] = Field(None, ge=30, le=150)
    blood_pressure_systolic: Optional[float] = Field(None, ge=60, le=250)
    blood_pressure_diastolic: Optional[float] = Field(None, ge=40, le=160)
    temperature: Optional[float] = Field(None, ge=34.0, le=42.0)
    oxygen_saturation: Optional[float] = Field(None, ge=50, le=100)
    respiratory_rate: Optional[float] = Field(None, ge=5, le=60)

    # Sleep
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[float] = Field(None, ge=0, le=100)

    # Fatigue / Stress
    stress_level: Optional[float] = Field(None, ge=0, le=10)
    fatigue_score: Optional[float] = Field(None, ge=0, le=100)
    alertness_score: Optional[float] = Field(None, ge=0, le=100)
    reaction_time_ms: Optional[float] = Field(None, ge=0, le=5000)

    # Cognitive
    cognitive_score: Optional[float] = Field(None, ge=0, le=100)
    memory_score: Optional[float] = Field(None, ge=0, le=100)
    attention_score: Optional[float] = Field(None, ge=0, le=100)

    notes: Optional[str] = None

class HealthRecordResponse(BaseModel):
    id: int
    user_id: int
    record_date: datetime
    heart_rate: Optional[float]
    resting_heart_rate: Optional[float]
    blood_pressure_systolic: Optional[float]
    blood_pressure_diastolic: Optional[float]
    temperature: Optional[float]
    oxygen_saturation: Optional[float]
    respiratory_rate: Optional[float]
    sleep_hours: Optional[float]
    sleep_quality: Optional[float]
    stress_level: Optional[float]
    fatigue_score: Optional[float]
    alertness_score: Optional[float]
    reaction_time_ms: Optional[float]
    cognitive_score: Optional[float]
    memory_score: Optional[float]
    attention_score: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/record", response_model=HealthRecordResponse, status_code=status.HTTP_201_CREATED)
def create_health_record(
    data: HealthRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a health record for a crew member."""
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You cannot submit health records.",
        )

    record = HealthRecord(
        user_id=data.user_id,
        heart_rate=data.heart_rate,
        resting_heart_rate=data.resting_heart_rate,
        blood_pressure_systolic=data.blood_pressure_systolic,
        blood_pressure_diastolic=data.blood_pressure_diastolic,
        temperature=data.temperature,
        oxygen_saturation=data.oxygen_saturation,
        respiratory_rate=data.respiratory_rate,
        sleep_hours=data.sleep_hours,
        sleep_quality=data.sleep_quality,
        stress_level=data.stress_level,
        fatigue_score=data.fatigue_score,
        alertness_score=data.alertness_score,
        reaction_time_ms=data.reaction_time_ms,
        cognitive_score=data.cognitive_score,
        memory_score=data.memory_score,
        attention_score=data.attention_score,
        notes=data.notes,
        created_by=current_user.id,
    )

    db.add(record)

    # Audit
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="health_record_created",
        resource_type="health_record",
        resource_id=str(data.user_id),
        action_details=f"Health record submitted for user {data.user_id}",
        module="Personnel Health Monitoring",
        success=True,
    ))

    db.commit()
    db.refresh(record)
    return record


@router.get("/history", response_model=List[HealthRecordResponse])
def get_health_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(30, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get health records. Supervisors see all; aviators see their own."""
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL) or has_permission(current_user, VIEW_CREW_DATA)

    query = db.query(HealthRecord)

    if user_id:
        if not can_view_all and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        query = query.filter(HealthRecord.user_id == user_id)
    elif not can_view_all:
        query = query.filter(HealthRecord.user_id == current_user.id)

    return query.order_by(desc(HealthRecord.record_date)).limit(limit).all()


@router.get("/latest/{user_id}", response_model=HealthRecordResponse)
def get_latest_health_record(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get most recent health record for a user."""
    can_view = has_permission(current_user, VIEW_CREW_DATA) or current_user.id == user_id
    if not can_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    record = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user_id)
        .order_by(desc(HealthRecord.record_date))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No health records found.")
    return record
