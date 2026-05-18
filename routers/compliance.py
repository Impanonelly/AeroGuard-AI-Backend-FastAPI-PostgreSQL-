from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import ComplianceCheck, User, UserRole, AuditLog, AlcoholScreening, SubstanceScreening, MedicalRecord, DutyPeriod, FitnessAssessment
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_COMPLIANCE, MANAGE_COMPLIANCE, VIEW_ALL_PERSONNEL

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class ComplianceCheckCreate(BaseModel):
    user_id: Optional[int] = None
    check_type: str  # rcaa_medical, duty_hours, alcohol_policy, substance_policy, frms
    regulation_reference: Optional[str] = None
    description: Optional[str] = None

class ComplianceCheckResponse(BaseModel):
    id: int
    user_id: Optional[int]
    check_date: datetime
    check_type: str
    regulation_reference: Optional[str]
    description: Optional[str]
    is_compliant: bool
    compliance_score: Optional[float]
    violations_found: int
    violation_details: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

RCAA_REGULATIONS = {
    "alcohol_policy": {
        "reference": "RCAA-OPS-CAR-AIR-014 § 4.2",
        "description": "Zero tolerance BAC for flight crew. BAC must be 0.00% before flight duty.",
    },
    "substance_policy": {
        "reference": "RCAA-OPS-CAR-AIR-014 § 4.3",
        "description": "Mandatory drug screening. All substances must return negative results.",
    },
    "duty_hours": {
        "reference": "RCAA-OPS-FTL-2023 § 3.1",
        "description": "Max 60 flight duty hours in 7 days. Max 190 hours in 28 days.",
    },
    "rcaa_medical": {
        "reference": "RCAA-MED-001 § 2.1 (ICAO Annex 1)",
        "description": "Valid ICAO Class 1 medical certificate required for commercial pilots.",
    },
    "frms": {
        "reference": "RCAA-OPS-FRMS-2023 (ICAO Doc 9966)",
        "description": "Fatigue Risk Management System compliance — cumulative fatigue monitoring.",
    },
}


def _run_alcohol_check(user_id: Optional[int], db: Session) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=30)
    q = db.query(AlcoholScreening).filter(AlcoholScreening.screening_date >= cutoff)
    if user_id:
        q = q.filter(AlcoholScreening.user_id == user_id)
    screenings = q.all()
    violations = [s for s in screenings if s.is_violation]
    score = round(((len(screenings) - len(violations)) / len(screenings) * 100) if screenings else 100.0, 1)
    return {
        "is_compliant": len(violations) == 0,
        "compliance_score": score,
        "violations_found": len(violations),
        "violation_details": str([f"BAC: {v.bac_level}% on {v.screening_date.date()}" for v in violations]) if violations else None,
    }


def _run_duty_hours_check(user_id: Optional[int], db: Session) -> dict:
    cutoff_7d = datetime.utcnow() - timedelta(days=7)
    q = db.query(DutyPeriod).filter(DutyPeriod.duty_start >= cutoff_7d, DutyPeriod.status == "completed")
    if user_id:
        q = q.filter(DutyPeriod.user_id == user_id)
    duties = q.all()
    total_7d = sum(d.duty_hours or 0 for d in duties)
    violations = []
    if total_7d > 60:
        violations.append(f"Exceeded 60h limit in 7 days: {total_7d:.1f}h logged")
    score = max(0, round(100 - max(0, total_7d - 60) * 5, 1))
    return {
        "is_compliant": len(violations) == 0,
        "compliance_score": score,
        "violations_found": len(violations),
        "violation_details": str(violations) if violations else None,
    }


def _run_medical_check(user_id: Optional[int], db: Session) -> dict:
    now = datetime.utcnow()
    q = db.query(MedicalRecord).filter(MedicalRecord.valid_until <= now)
    if user_id:
        q = q.filter(MedicalRecord.user_id == user_id)
    expired = q.count()
    total = db.query(MedicalRecord).count() if not user_id else db.query(MedicalRecord).filter(MedicalRecord.user_id == user_id).count()
    score = round(((total - expired) / total * 100) if total else 100.0, 1)
    return {
        "is_compliant": expired == 0,
        "compliance_score": score,
        "violations_found": expired,
        "violation_details": f"{expired} expired medical certificate(s) found." if expired else None,
    }

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/summary")
def get_compliance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Overall RCAA compliance summary across all domains."""
    if not has_permission(current_user, VIEW_COMPLIANCE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    alcohol    = _run_alcohol_check(None, db)
    duty_hours = _run_duty_hours_check(None, db)
    medical    = _run_medical_check(None, db)

    checks = [alcohol, duty_hours, medical]
    total_violations = sum(c["violations_found"] for c in checks)
    avg_score = round(sum(c["compliance_score"] for c in checks) / len(checks), 1)
    overall_compliant = all(c["is_compliant"] for c in checks)

    return {
        "overall_compliant": overall_compliant,
        "overall_score": avg_score,
        "total_violations": total_violations,
        "domains": {
            "alcohol_policy":  {**alcohol,    "regulation": RCAA_REGULATIONS["alcohol_policy"]["reference"]},
            "duty_hours":      {**duty_hours,  "regulation": RCAA_REGULATIONS["duty_hours"]["reference"]},
            "rcaa_medical":    {**medical,     "regulation": RCAA_REGULATIONS["rcaa_medical"]["reference"]},
        },
        "rcaa_framework": "Rwanda Civil Aviation Authority Operational Safety Requirements",
    }


@router.post("/check/{user_id}")
def run_compliance_check(
    user_id: int,
    data: ComplianceCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a specific compliance check for a user and persist the result."""
    if not has_permission(current_user, MANAGE_COMPLIANCE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Safety Officer role required.")

    reg = RCAA_REGULATIONS.get(data.check_type, {})

    if data.check_type == "alcohol_policy":
        result = _run_alcohol_check(user_id, db)
    elif data.check_type == "duty_hours":
        result = _run_duty_hours_check(user_id, db)
    elif data.check_type == "rcaa_medical":
        result = _run_medical_check(user_id, db)
    else:
        result = {"is_compliant": True, "compliance_score": 100.0, "violations_found": 0, "violation_details": None}

    check = ComplianceCheck(
        user_id=user_id,
        check_type=data.check_type,
        regulation_reference=data.regulation_reference or reg.get("reference"),
        description=data.description or reg.get("description"),
        checked_by=current_user.id,
        status="open" if not result["is_compliant"] else "resolved",
        **result,
    )
    db.add(check)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="compliance_check_run",
        resource_type="compliance_check",
        resource_id=str(user_id),
        action_details=f"Check: {data.check_type} | Compliant: {result['is_compliant']} | Score: {result['compliance_score']}",
        module="Compliance",
        success=True,
    ))
    db.commit()
    db.refresh(check)
    return check


@router.get("/violations")
def get_violations(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active compliance violations."""
    if not has_permission(current_user, VIEW_COMPLIANCE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    violations = db.query(ComplianceCheck).filter(
        ComplianceCheck.check_date >= cutoff,
        ComplianceCheck.is_compliant == False,
        ComplianceCheck.status.in_(["open", "under_review", "escalated"])
    ).order_by(desc(ComplianceCheck.check_date)).all()

    return {
        "total_violations": len(violations),
        "violations": [
            {
                "id": v.id,
                "user_id": v.user_id,
                "check_type": v.check_type,
                "regulation": v.regulation_reference,
                "compliance_score": v.compliance_score,
                "violation_details": v.violation_details,
                "status": v.status,
                "check_date": v.check_date,
            }
            for v in violations
        ],
    }


@router.get("/crew")
def get_crew_compliance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-crew-member compliance overview."""
    if not has_permission(current_user, VIEW_ALL_PERSONNEL):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).all()
    result = []
    for av in aviators:
        alcohol = _run_alcohol_check(av.id, db)
        duty    = _run_duty_hours_check(av.id, db)
        medical = _run_medical_check(av.id, db)
        avg_score = round((alcohol["compliance_score"] + duty["compliance_score"] + medical["compliance_score"]) / 3, 1)
        result.append({
            "user_id": av.id,
            "full_name": av.full_name,
            "employee_id": av.employee_id,
            "overall_score": avg_score,
            "is_compliant": alcohol["is_compliant"] and duty["is_compliant"] and medical["is_compliant"],
            "alcohol_compliant": alcohol["is_compliant"],
            "duty_hours_compliant": duty["is_compliant"],
            "medical_compliant": medical["is_compliant"],
        })

    return {"crew_compliance": result, "total": len(result)}
