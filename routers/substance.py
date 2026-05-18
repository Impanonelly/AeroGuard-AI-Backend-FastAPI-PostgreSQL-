from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import SubstanceScreening, User, DutyPeriod, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL, SUBMIT_ASSESSMENT
from pydantic import BaseModel, Field

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class SubstanceScreeningCreate(BaseModel):
    user_id: int
    screening_type: str = Field(default="random", description="pre_flight | random | scheduled")
    
    cannabis_result: str = "negative"
    opioids_result: str = "negative"
    cocaine_result: str = "negative"
    amphetamines_result: str = "negative"
    benzodiazepines_result: str = "negative"
    
    test_method: str = "urine"
    laboratory_id: Optional[str] = None
    report_number: Optional[str] = None
    notes: Optional[str] = None

class SubstanceScreeningResponse(BaseModel):
    id: int
    user_id: int
    screening_date: datetime
    screening_type: str
    cannabis_result: str
    opioids_result: str
    cocaine_result: str
    amphetamines_result: str
    benzodiazepines_result: str
    test_method: str
    result_status: str
    is_violation: bool
    violation_details: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def classify_substance_results(data: SubstanceScreeningCreate) -> tuple[str, bool, Optional[str]]:
    """Returns (result_status, is_violation, violation_details)"""
    results = [data.cannabis_result, data.opioids_result, data.cocaine_result, data.amphetamines_result, data.benzodiazepines_result]
    
    if any(r == "positive" for r in results):
        positives = []
        if data.cannabis_result == "positive": positives.append("Cannabis")
        if data.opioids_result == "positive": positives.append("Opioids")
        if data.cocaine_result == "positive": positives.append("Cocaine")
        if data.amphetamines_result == "positive": positives.append("Amphetamines")
        if data.benzodiazepines_result == "positive": positives.append("Benzodiazepines")
        
        return "flagged", True, f"Positive result for: {', '.join(positives)}. Immediate grounding required."
    
    if any(r == "trace" for r in results):
        return "pending", False, "Trace levels detected. Secondary laboratory confirmation required."
        
    return "cleared", False, None

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/screening", response_model=SubstanceScreeningResponse, status_code=status.HTTP_201_CREATED)
def record_substance_screening(
    data: SubstanceScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a substance test result.
    - Any 'positive' → FLAGGED (automatic grounding)
    - Any 'trace' → PENDING (manual review required)
    - All 'negative' → CLEARED
    """
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You cannot submit substance screenings.",
        )

    result_status, is_violation, violation_details = classify_substance_results(data)

    screening = SubstanceScreening(
        user_id=data.user_id,
        screening_type=data.screening_type,
        cannabis_result=data.cannabis_result,
        opioids_result=data.opioids_result,
        cocaine_result=data.cocaine_result,
        amphetamines_result=data.amphetamines_result,
        benzodiazepines_result=data.benzodiazepines_result,
        test_method=data.test_method,
        laboratory_id=data.laboratory_id,
        report_number=data.report_number,
        result_status=result_status,
        is_violation=is_violation,
        violation_details=violation_details,
        supervised_by=current_user.id,
        notes=data.notes,
    )

    db.add(screening)

    # If flagged (violation), cancel any active duty periods
    if is_violation:
        active_duties = db.query(DutyPeriod).filter(
            DutyPeriod.user_id == data.user_id,
            DutyPeriod.status == "active",
        ).all()
        for duty in active_duties:
            duty.status = "cancelled"
            duty.notes = f"Auto-cancelled: Substance violation ({violation_details})"

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action_type="substance_screening",
        resource_type="substance_screening",
        resource_id=str(data.user_id),
        action_details=f"Substance Test → {result_status.upper()}",
        module="Alcohol & Substance",
        success=True,
    )
    db.add(audit)
    db.commit()
    db.refresh(screening)

    return screening

@router.get("/history", response_model=List[SubstanceScreeningResponse])
def get_substance_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get substance screening history."""
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL) or has_permission(current_user, VIEW_CREW_DATA)

    query = db.query(SubstanceScreening)

    if user_id:
        if not can_view_all and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        query = query.filter(SubstanceScreening.user_id == user_id)
    elif not can_view_all:
        query = query.filter(SubstanceScreening.user_id == current_user.id)

    return query.order_by(desc(SubstanceScreening.screening_date)).limit(limit).all()
