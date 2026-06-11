from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import AlcoholScreening, User, DutyPeriod, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL, SUBMIT_ASSESSMENT
from pydantic import BaseModel, Field

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class AlcoholScreeningCreate(BaseModel):
    user_id: int
    screening_type: str = Field(default="pre_flight", description="pre_flight | post_flight | random | scheduled")
    bac_level: float = Field(..., ge=0.0, le=1.0, description="Blood Alcohol Content %")
    test_method: str = Field(default="breathalyzer", description="breathalyzer | blood | urine")
    device_id: Optional[str] = None
    witness_name: Optional[str] = None
    test_location: Optional[str] = None
    notes: Optional[str] = None

class AlcoholScreeningResponse(BaseModel):
    id: int
    user_id: int
    screening_date: datetime
    screening_type: str
    bac_level: float
    test_method: str
    result_status: str
    is_violation: bool
    violation_details: Optional[str]
    witness_name: Optional[str]
    test_location: Optional[str]
    notes: Optional[str]
    created_at: datetime
    device_id: Optional[str] = "AlcoQuant 6020 Plus"

    class Config:
        from_attributes = True

# BAC thresholds (ICAO / Rwanda CAA)
BAC_CLEAR_LIMIT = 0.00     # zero tolerance for on-duty aviators
BAC_GROUNDING_THRESHOLD = 0.02  # automatic grounding above this

def classify_bac(bac: float) -> tuple[str, bool, Optional[str]]:
    """Returns (result_status, is_violation, violation_details)"""
    if bac == 0.00:
        return "cleared", False, None
    elif bac < BAC_GROUNDING_THRESHOLD:
        return "warning", False, f"BAC {bac:.3f}% detected — below grounding threshold but above zero. Monitor closely."
    else:
        return "grounded", True, (
            f"BAC {bac:.3f}% exceeds regulatory limit ({BAC_GROUNDING_THRESHOLD}%). "
            "Automatic grounding initiated per ICAO Annex 1 and Rwanda CAA regulations."
        )

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/screening", response_model=AlcoholScreeningResponse, status_code=status.HTTP_201_CREATED)
def record_alcohol_screening(
    data: AlcoholScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a BAC test result.
    - BAC == 0.00 → CLEARED
    - BAC < 0.02  → WARNING
    - BAC >= 0.02 → GROUNDED (automatic grounding, duty blocked)
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You cannot submit alcohol screenings.",
        )

    result_status, is_violation, violation_details = classify_bac(data.bac_level)

    notes_with_device = data.notes or ""
    if data.device_id:
        notes_with_device = f"{notes_with_device} [Device: {data.device_id}]".strip()

    screening = AlcoholScreening(
        user_id=data.user_id,
        screening_type=data.screening_type,
        bac_level=data.bac_level,
        test_method=data.test_method,
        result_status=result_status,
        is_violation=is_violation,
        violation_details=violation_details,
        witness_name=data.witness_name,
        supervised_by=current_user.id,
        test_location=data.test_location,
        notes=notes_with_device,
    )

    db.add(screening)

    # If grounded, cancel any active duty periods for this user
    if is_violation:
        active_duties = db.query(DutyPeriod).filter(
            DutyPeriod.user_id == data.user_id,
            DutyPeriod.status == "active",
        ).all()
        for duty in active_duties:
            duty.status = "cancelled"
            duty.notes = f"Auto-cancelled: alcohol violation (BAC {data.bac_level:.3f}%)"

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action_type="alcohol_screening",
        resource_type="alcohol_screening",
        resource_id=str(data.user_id),
        action_details=f"BAC Test: {data.bac_level:.3f}% → {result_status.upper()}",
        module="Alcohol & Substance",
        success=True,
    )
    db.add(audit)
    db.commit()
    db.refresh(screening)

    return screening


@router.get("/history", response_model=List[AlcoholScreeningResponse])
def get_alcohol_history(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alcohol screening history. Supervisors see all; aviators see their own."""
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL) or has_permission(current_user, VIEW_CREW_DATA)

    query = db.query(AlcoholScreening)

    if user_id:
        if not can_view_all and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other users' records.")
        query = query.filter(AlcoholScreening.user_id == user_id)
    elif not can_view_all:
        query = query.filter(AlcoholScreening.user_id == current_user.id)

    return query.order_by(desc(AlcoholScreening.screening_date)).limit(limit).all()


@router.get("/violations", response_model=List[AlcoholScreeningResponse])
def get_violations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all alcohol violations. Requires supervisor or above."""
    if not has_permission(current_user, VIEW_ALL_PERSONNEL):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor access required.")
    violations = (
        db.query(AlcoholScreening)
        .filter(AlcoholScreening.is_violation == True)
        .order_by(desc(AlcoholScreening.screening_date))
        .all()
    )
    return violations


@router.get("/today-stats")
def get_today_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get today's testing statistics (dashboard summary)."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    screenings = db.query(AlcoholScreening).filter(AlcoholScreening.screening_date >= today_start).all()
    total = len(screenings)
    cleared = sum(1 for s in screenings if s.result_status == "cleared")
    violations = sum(1 for s in screenings if s.is_violation)
    return {
        "total_tests_today": total,
        "cleared": cleared,
        "warnings": total - cleared - violations,
        "violations": violations,
        "compliance_rate": round((cleared / total * 100) if total > 0 else 100.0, 1),
    }
