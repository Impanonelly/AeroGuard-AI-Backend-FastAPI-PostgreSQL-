from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from database import get_db
from models import User, FitnessAssessment, AlcoholScreening, SubstanceScreening, UserRole, AuditLog, MedicalRecord
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL, require_role
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class AviatorStatus(BaseModel):
    id: int
    full_name: str
    employee_id: str
    role: str
    
    # Latest Status
    risk_level: str = "LOW"
    clearance_status: str = "grounded"
    clearance_level: str = "red"
    
    # Metrics
    last_assessment_date: Optional[datetime] = None
    alertness_score: Optional[float] = None
    fatigue_score: Optional[float] = None
    
    # Compliance Gates
    alcohol_cleared: bool = False
    substance_cleared: bool = False

    # Apple Watch Telemetry
    apple_watch_sleep_hours: Optional[float] = None
    apple_watch_sleep_quality: Optional[float] = None
    apple_watch_resting_hr: Optional[float] = None
    apple_watch_current_hr: Optional[float] = None
    apple_watch_activity_level: Optional[float] = None

    # Pre-Flight Self Assessment
    self_alertness_level: Optional[float] = None
    alcohol_declared: bool = False

    # Reaction Time
    reaction_time_ms: Optional[float] = None

    # Medical Record Status integration
    medical_certificate_status: Optional[str] = "No Record"
    medical_class: Optional[str] = "None"
    medical_valid_until: Optional[datetime] = None
    medical_limitations: Optional[str] = None
    medical_is_valid: bool = False
    
    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/", response_model=List[AviatorStatus])
def get_all_aviators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unified endpoint for personnel monitoring.
    Fetches all aviators and their latest safety statuses.
    """
    if not (has_permission(current_user, VIEW_CREW_DATA) or has_permission(current_user, VIEW_ALL_PERSONNEL)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    aviators = db.query(User).filter(User.role == UserRole.AVIATOR).all()
    results = []

    for aviator in aviators:
        # Get latest fitness assessment
        latest_assessment = (
            db.query(FitnessAssessment)
            .filter(FitnessAssessment.user_id == aviator.id)
            .order_by(desc(FitnessAssessment.assessment_date))
            .first()
        )

        # Get latest alcohol screening (last 12h)
        latest_alcohol = (
            db.query(AlcoholScreening)
            .filter(AlcoholScreening.user_id == aviator.id)
            .order_by(desc(AlcoholScreening.screening_date))
            .first()
        )
        alcohol_ok = latest_alcohol.result_status == "cleared" if latest_alcohol else False

        # Get latest substance screening
        latest_substance = (
            db.query(SubstanceScreening)
            .filter(SubstanceScreening.user_id == aviator.id)
            .order_by(desc(SubstanceScreening.screening_date))
            .first()
        )
        substance_ok = latest_substance.result_status == "cleared" if latest_substance else False

        # Get latest medical certificate details
        latest_medical = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.user_id == aviator.id)
            .order_by(desc(MedicalRecord.record_date))
            .first()
        )
        medical_is_valid = False
        med_cert_status = "No Record"
        med_class = "None"
        med_valid_until = None
        med_limitations = None
        
        if latest_medical:
            med_class = latest_medical.medical_class or "None"
            med_valid_until = latest_medical.valid_until
            med_limitations = latest_medical.limitations
            if latest_medical.clearance_status == "cleared":
                if not latest_medical.valid_until or latest_medical.valid_until >= datetime.utcnow():
                    medical_is_valid = True
                    med_cert_status = "Cleared / Valid Certificate"
                else:
                    med_cert_status = "Expired Certificate"
            else:
                med_cert_status = f"Restricted/Suspended ({latest_medical.clearance_status})"

        status = AviatorStatus(
            id=aviator.id,
            full_name=aviator.full_name,
            employee_id=aviator.employee_id,
            role=aviator.role,
            risk_level=latest_assessment.risk_level if latest_assessment else "LOW",
            clearance_status=latest_assessment.clearance_status if latest_assessment else "grounded",
            clearance_level=latest_assessment.clearance_level if latest_assessment else "red",
            last_assessment_date=latest_assessment.assessment_date if latest_assessment else None,
            alertness_score=latest_assessment.overall_score if latest_assessment else None,
            fatigue_score=latest_assessment.fatigue_score if latest_assessment else None,
            alcohol_cleared=alcohol_ok,
            substance_cleared=substance_ok,
            
            # Apple Watch
            apple_watch_sleep_hours=latest_assessment.apple_watch_sleep_hours if latest_assessment else None,
            apple_watch_sleep_quality=latest_assessment.apple_watch_sleep_quality if latest_assessment else None,
            apple_watch_resting_hr=latest_assessment.apple_watch_resting_hr if latest_assessment else None,
            apple_watch_current_hr=latest_assessment.apple_watch_current_hr if latest_assessment else None,
            apple_watch_activity_level=latest_assessment.apple_watch_activity_level if latest_assessment else None,
            
            # Pre-flight
            self_alertness_level=latest_assessment.self_alertness_level if latest_assessment else None,
            alcohol_declared=latest_assessment.alcohol_declared if latest_assessment else False,
            reaction_time_ms=latest_assessment.reaction_time_ms if latest_assessment else None,
            
            # Medical Record Integration
            medical_certificate_status=med_cert_status,
            medical_class=med_class,
            medical_valid_until=med_valid_until,
            medical_limitations=med_limitations,
            medical_is_valid=medical_is_valid
        )
        results.append(status)

    return results

class ReadinessActionRequest(BaseModel):
    action: str  # "validate", "restrict", "reassess"
    reason: Optional[str] = None

@router.post("/{user_id}/status")
def update_readiness_status(
    user_id: int,
    request: ReadinessActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.MEDICAL_OFFICER, UserRole.ADMINISTRATOR, UserRole.SUPERVISOR]))
):
    """
    Secure endpoint for Medical Officers to validate, restrict, or reassess personnel readiness.
    Logs all actions to the Audit Log.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Personnel not found")

    latest_assessment = (
        db.query(FitnessAssessment)
        .filter(FitnessAssessment.user_id == user_id)
        .order_by(desc(FitnessAssessment.assessment_date))
        .first()
    )

    if not latest_assessment:
        raise HTTPException(status_code=404, detail="No fitness assessment records found for this personnel")

    old_status = latest_assessment.clearance_status

    if request.action == "validate":
        latest_assessment.clearance_status = "cleared"
        latest_assessment.clearance_level = "green"
    elif request.action == "restrict":
        latest_assessment.clearance_status = "conditional"
        latest_assessment.clearance_level = "yellow"
    elif request.action == "reassess":
        latest_assessment.clearance_status = "conditional"
        latest_assessment.clearance_level = "yellow"
    elif request.action in ("grounded", "ground"):
        latest_assessment.clearance_status = "grounded"
        latest_assessment.clearance_level = "red"
    else:
        raise HTTPException(status_code=400, detail="Invalid action provided")

    # Create immutable audit log entry
    audit = AuditLog(
        user_id=current_user.id,
        action_type=f"readiness_{request.action}",
        resource_type="personnel",
        resource_id=str(user_id),
        action_details=f"Status changed from {old_status} to {latest_assessment.clearance_status}. Reason: {request.reason or 'N/A'}",
        module="Operational Readiness",
        success=True
    )

    db.add(audit)
    db.commit()

    return {"status": "success", "new_status": latest_assessment.clearance_status}
