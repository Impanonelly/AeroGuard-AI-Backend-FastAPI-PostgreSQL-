from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import FRMSEntry, DutyPeriod, HealthRecord, AlertnessReading, User, UserRole, AuditLog, Notification
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_FRMS_DATA, MANAGE_FRMS, VIEW_CREW_DATA

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class FRMSEntryCreate(BaseModel):
    user_id: int
    entry_type: str = "daily_log"
    cumulative_fatigue_score: Optional[float] = Field(None, ge=0, le=100)
    sleep_debt_hours: Optional[float] = None
    circadian_phase: Optional[str] = "normal"
    wake_hours: Optional[float] = None
    duty_hours_7d: Optional[float] = None
    duty_hours_28d: Optional[float] = None
    night_duties_7d: Optional[int] = None
    biomathematical_score: Optional[float] = None
    alertness_window: Optional[str] = None
    intervention_type: Optional[str] = None
    notes: Optional[str] = None

class FRMSEntryResponse(BaseModel):
    id: int
    user_id: int
    entry_date: datetime
    entry_type: str
    cumulative_fatigue_score: Optional[float]
    sleep_debt_hours: Optional[float]
    circadian_phase: Optional[str]
    wake_hours: Optional[float]
    duty_hours_7d: Optional[float]
    duty_hours_28d: Optional[float]
    night_duties_7d: Optional[int]
    predicted_fatigue_level: str
    biomathematical_score: Optional[float]
    alertness_window: Optional[str]
    frms_status: str
    intervention_required: bool
    intervention_type: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _classify_frms(fatigue_score: Optional[float], duty_7d: Optional[float], sleep_debt: Optional[float]) -> dict:
    """Determine FRMS status and fatigue level."""
    score = fatigue_score or 0
    duty = duty_7d or 0
    debt = sleep_debt or 0

    # ICAO / FRMS regulatory thresholds
    if score >= 80 or duty > 55 or debt > 10:
        return {"predicted_fatigue_level": "CRITICAL", "frms_status": "critical", "intervention_required": True}
    elif score >= 60 or duty > 45 or debt > 6:
        return {"predicted_fatigue_level": "HIGH", "frms_status": "warning", "intervention_required": True}
    elif score >= 40 or duty > 35 or debt > 3:
        return {"predicted_fatigue_level": "MEDIUM", "frms_status": "watch", "intervention_required": False}
    else:
        return {"predicted_fatigue_level": "LOW", "frms_status": "normal", "intervention_required": False}

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/log", response_model=FRMSEntryResponse, status_code=status.HTTP_201_CREATED)
def log_frms_entry(
    data: FRMSEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a new FRMS daily entry or event."""
    if not has_permission(current_user, MANAGE_FRMS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    classification = _classify_frms(data.cumulative_fatigue_score, data.duty_hours_7d, data.sleep_debt_hours)

    entry = FRMSEntry(
        user_id=data.user_id,
        entry_type=data.entry_type,
        cumulative_fatigue_score=data.cumulative_fatigue_score,
        sleep_debt_hours=data.sleep_debt_hours,
        circadian_phase=data.circadian_phase,
        wake_hours=data.wake_hours,
        duty_hours_7d=data.duty_hours_7d,
        duty_hours_28d=data.duty_hours_28d,
        night_duties_7d=data.night_duties_7d,
        biomathematical_score=data.biomathematical_score,
        alertness_window=data.alertness_window,
        intervention_type=data.intervention_type,
        notes=data.notes,
        logged_by=current_user.id,
        **classification,
    )
    db.add(entry)

    if classification["intervention_required"]:
        db.add(Notification(
            user_id=data.user_id,
            title=f"🟠 FRMS Alert — {classification['predicted_fatigue_level']} Fatigue",
            message=f"FRMS status: {classification['frms_status'].upper()}. Fatigue level: {classification['predicted_fatigue_level']}. Immediate review required.",
            notification_type="warning",
            priority="critical" if classification["frms_status"] == "critical" else "high",
            action_required=True,
        ))

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="frms_entry_logged",
        resource_type="frms_entry",
        resource_id=str(data.user_id),
        action_details=f"FRMS: {classification['frms_status']} | Fatigue: {classification['predicted_fatigue_level']}",
        module="FRMS Monitoring",
        success=True,
    ))
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/dashboard")
def get_frms_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FRMS dashboard — fleet fatigue overview and regulatory summary."""
    if not has_permission(current_user, VIEW_FRMS_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff_7d = datetime.utcnow() - timedelta(days=7)
    entries = db.query(FRMSEntry).filter(FRMSEntry.entry_date >= cutoff_7d).all()

    normal   = sum(1 for e in entries if e.frms_status == "normal")
    watch    = sum(1 for e in entries if e.frms_status == "watch")
    warning  = sum(1 for e in entries if e.frms_status == "warning")
    critical = sum(1 for e in entries if e.frms_status == "critical")
    interventions_needed = sum(1 for e in entries if e.intervention_required)

    avg_fatigue = round(sum(e.cumulative_fatigue_score or 0 for e in entries) / len(entries), 1) if entries else 0.0

    # Duty hour regulatory check (ICAO: max 60h / 7 days)
    duty_violations = db.query(FRMSEntry).filter(
        FRMSEntry.entry_date >= cutoff_7d,
        FRMSEntry.duty_hours_7d > 60
    ).count()

    return {
        "period_days": 7,
        "total_entries": len(entries),
        "average_cumulative_fatigue": avg_fatigue,
        "status_distribution": {
            "normal": normal, "watch": watch, "warning": warning, "critical": critical
        },
        "interventions_required": interventions_needed,
        "duty_hour_violations_7d": duty_violations,
        "regulatory_reference": "ICAO Doc 9966 — Fatigue Risk Management Systems Manual",
    }


@router.get("/crew-status")
def get_crew_frms_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All crew members' current FRMS status (latest entry per person)."""
    if not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).all()
    result = []
    for av in aviators:
        latest = db.query(FRMSEntry).filter(
            FRMSEntry.user_id == av.id
        ).order_by(desc(FRMSEntry.entry_date)).first()

        result.append({
            "user_id": av.id,
            "full_name": av.full_name,
            "employee_id": av.employee_id,
            "frms_status": latest.frms_status if latest else "no_data",
            "predicted_fatigue_level": latest.predicted_fatigue_level if latest else "unknown",
            "cumulative_fatigue_score": latest.cumulative_fatigue_score if latest else None,
            "last_entry": latest.entry_date if latest else None,
            "intervention_required": latest.intervention_required if latest else False,
        })

    return {"crew": result, "total": len(result)}


@router.get("/alerts")
def get_frms_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Active FRMS fatigue alerts requiring intervention."""
    if not has_permission(current_user, VIEW_FRMS_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(hours=48)
    alerts = db.query(FRMSEntry).filter(
        FRMSEntry.entry_date >= cutoff,
        FRMSEntry.intervention_required == True
    ).order_by(desc(FRMSEntry.entry_date)).all()

    return {
        "active_alerts": len(alerts),
        "alerts": [
            {
                "entry_id": a.id,
                "user_id": a.user_id,
                "frms_status": a.frms_status,
                "fatigue_level": a.predicted_fatigue_level,
                "cumulative_fatigue": a.cumulative_fatigue_score,
                "intervention_type": a.intervention_type,
                "logged_at": a.entry_date,
            }
            for a in alerts
        ]
    }


@router.get("/history/{user_id}", response_model=List[FRMSEntryResponse])
def get_frms_history(
    user_id: int,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FRMS history for a user."""
    if not has_permission(current_user, VIEW_FRMS_DATA) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    return db.query(FRMSEntry).filter(
        FRMSEntry.user_id == user_id,
        FRMSEntry.entry_date >= cutoff,
    ).order_by(desc(FRMSEntry.entry_date)).all()
