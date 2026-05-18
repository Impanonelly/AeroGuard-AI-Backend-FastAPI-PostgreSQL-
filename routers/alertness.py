from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import AlertnessReading, User, AuditLog, Notification
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_ALERTNESS_DATA, SUBMIT_ALERTNESS_READING, VIEW_CREW_DATA

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class AlertnessReadingCreate(BaseModel):
    user_id: int
    alertness_score: float = Field(..., ge=0, le=100)
    fatigue_index: Optional[float] = Field(None, ge=0, le=100)
    reaction_time_ms: Optional[float] = None
    blink_rate: Optional[float] = None
    eye_closure_duration: Optional[float] = None
    cognitive_load: Optional[float] = Field(None, ge=0, le=100)
    attention_score: Optional[float] = Field(None, ge=0, le=100)
    heart_rate: Optional[float] = None
    hrv_score: Optional[float] = None
    eeg_theta_power: Optional[float] = None
    eeg_alpha_power: Optional[float] = None
    source: str = "manual"
    device_id: Optional[str] = None

class AlertnessReadingResponse(BaseModel):
    id: int
    user_id: int
    reading_timestamp: datetime
    source: str
    alertness_score: float
    fatigue_index: Optional[float]
    reaction_time_ms: Optional[float]
    blink_rate: Optional[float]
    eye_closure_duration: Optional[float]
    cognitive_load: Optional[float]
    attention_score: Optional[float]
    heart_rate: Optional[float]
    hrv_score: Optional[float]
    alertness_level: str
    risk_flag: bool
    device_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _classify_alertness(score: float) -> tuple[str, bool]:
    """Returns (alertness_level, risk_flag)"""
    if score >= 80:
        return "high", False
    elif score >= 60:
        return "moderate", False
    elif score >= 40:
        return "low", True
    else:
        return "critical", True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/reading", response_model=AlertnessReadingResponse, status_code=status.HTTP_201_CREATED)
def submit_alertness_reading(
    data: AlertnessReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a new alertness reading (manual or from IoT device)."""
    if not has_permission(current_user, SUBMIT_ALERTNESS_READING):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    alertness_level, risk_flag = _classify_alertness(data.alertness_score)

    reading = AlertnessReading(
        user_id=data.user_id,
        alertness_score=data.alertness_score,
        fatigue_index=data.fatigue_index,
        reaction_time_ms=data.reaction_time_ms,
        blink_rate=data.blink_rate,
        eye_closure_duration=data.eye_closure_duration,
        cognitive_load=data.cognitive_load,
        attention_score=data.attention_score,
        heart_rate=data.heart_rate,
        hrv_score=data.hrv_score,
        eeg_theta_power=data.eeg_theta_power,
        eeg_alpha_power=data.eeg_alpha_power,
        source=data.source,
        device_id=data.device_id,
        alertness_level=alertness_level,
        risk_flag=risk_flag,
    )
    db.add(reading)

    # Auto-generate notification if risk flag raised
    if risk_flag:
        db.add(Notification(
            user_id=data.user_id,
            title=f"⚠️ Low Alertness Detected",
            message=f"Alertness score {data.alertness_score:.0f}/100 — classified as '{alertness_level.upper()}'. Supervisor review recommended.",
            notification_type="alert",
            priority="high" if alertness_level == "low" else "critical",
            action_required=True,
        ))

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="alertness_reading_submitted",
        resource_type="alertness_reading",
        resource_id=str(data.user_id),
        action_details=f"Alertness: {data.alertness_score} | Level: {alertness_level} | Risk: {risk_flag}",
        module="Alertness & Fatigue",
        success=True,
    ))
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/current/{user_id}", response_model=AlertnessReadingResponse)
def get_current_alertness(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent alertness reading for a user."""
    if not has_permission(current_user, VIEW_ALERTNESS_DATA) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    reading = (
        db.query(AlertnessReading)
        .filter(AlertnessReading.user_id == user_id)
        .order_by(desc(AlertnessReading.reading_timestamp))
        .first()
    )
    if not reading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No alertness readings found.")
    return reading


@router.get("/history/{user_id}", response_model=List[AlertnessReadingResponse])
def get_alertness_history(
    user_id: int,
    days: int = Query(7, le=90),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alertness reading history for trend analysis."""
    if not has_permission(current_user, VIEW_ALERTNESS_DATA) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    readings = (
        db.query(AlertnessReading)
        .filter(
            AlertnessReading.user_id == user_id,
            AlertnessReading.reading_timestamp >= cutoff,
        )
        .order_by(desc(AlertnessReading.reading_timestamp))
        .limit(limit)
        .all()
    )
    return readings


@router.get("/fleet")
def get_fleet_alertness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fleet-wide alertness overview (Supervisor / Safety Officer)."""
    if not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(hours=12)
    readings = db.query(AlertnessReading).filter(
        AlertnessReading.reading_timestamp >= cutoff
    ).all()

    high = sum(1 for r in readings if r.alertness_level == "high")
    moderate = sum(1 for r in readings if r.alertness_level == "moderate")
    low = sum(1 for r in readings if r.alertness_level == "low")
    critical = sum(1 for r in readings if r.alertness_level == "critical")
    risk_flags = sum(1 for r in readings if r.risk_flag)
    avg_score = round(sum(r.alertness_score for r in readings) / len(readings), 1) if readings else 0.0

    return {
        "period_hours": 12,
        "total_readings": len(readings),
        "average_alertness_score": avg_score,
        "distribution": {
            "high": high,
            "moderate": moderate,
            "low": low,
            "critical": critical,
        },
        "risk_flags_raised": risk_flags,
    }


@router.get("/trend-summary/{user_id}")
def get_alertness_trend_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """7-day alertness trend summary for a user."""
    if not has_permission(current_user, VIEW_ALERTNESS_DATA) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    daily = []
    for i in range(6, -1, -1):
        day_start = datetime.utcnow() - timedelta(days=i+1)
        day_end   = datetime.utcnow() - timedelta(days=i)
        readings = db.query(AlertnessReading).filter(
            AlertnessReading.user_id == user_id,
            AlertnessReading.reading_timestamp >= day_start,
            AlertnessReading.reading_timestamp < day_end,
        ).all()
        avg = round(sum(r.alertness_score for r in readings) / len(readings), 1) if readings else None
        daily.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "avg_alertness": avg,
            "readings_count": len(readings),
            "risk_flags": sum(1 for r in readings if r.risk_flag),
        })

    return {"user_id": user_id, "trend": daily}
