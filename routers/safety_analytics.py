from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import SafetyIncident, User, UserRole, AuditLog, AlcoholScreening, FitnessAssessment, DutyPeriod
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_SAFETY_ANALYTICS, REPORT_SAFETY_INCIDENT, MANAGE_SAFETY_INCIDENTS, VIEW_CREW_DATA

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class IncidentCreate(BaseModel):
    incident_date: datetime
    incident_type: str  # fatigue, alcohol, medical, operational, near_miss, equipment
    severity: str = "low"  # low, medium, high, critical
    title: str = Field(..., min_length=5)
    description: str = Field(..., min_length=20)
    involved_user_id: Optional[int] = None
    location: Optional[str] = None
    flight_number: Optional[str] = None
    aircraft_type: Optional[str] = None
    phase_of_flight: Optional[str] = None
    is_confidential: bool = False

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    rcaa_reported: Optional[bool] = None
    rcaa_reference: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    reporter_id: int
    involved_user_id: Optional[int]
    incident_date: datetime
    report_date: datetime
    incident_type: str
    severity: str
    title: str
    description: str
    location: Optional[str]
    flight_number: Optional[str]
    aircraft_type: Optional[str]
    phase_of_flight: Optional[str]
    status: str
    root_cause: Optional[str]
    corrective_action: Optional[str]
    rcaa_reported: bool
    rcaa_reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/kpis")
def get_safety_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Key safety performance indicators for the safety analytics dashboard."""
    if not has_permission(current_user, VIEW_SAFETY_ANALYTICS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    now = datetime.utcnow()
    d7  = now - timedelta(days=7)
    d30 = now - timedelta(days=30)
    d90 = now - timedelta(days=90)

    incidents_7d  = db.query(SafetyIncident).filter(SafetyIncident.incident_date >= d7).all()
    incidents_30d = db.query(SafetyIncident).filter(SafetyIncident.incident_date >= d30).all()
    incidents_90d = db.query(SafetyIncident).filter(SafetyIncident.incident_date >= d90).all()

    alcohol_violations_30d = db.query(AlcoholScreening).filter(
        AlcoholScreening.is_violation == True,
        AlcoholScreening.screening_date >= d30
    ).count()

    assessments_30d = db.query(FitnessAssessment).filter(FitnessAssessment.assessment_date >= d30).all()
    grounded_30d = sum(1 for a in assessments_30d if a.clearance_status == "grounded")
    compliance_rate = round(
        ((len(assessments_30d) - grounded_30d) / len(assessments_30d) * 100) if assessments_30d else 100.0, 1
    )

    critical_incidents = sum(1 for i in incidents_30d if i.severity == "critical")
    open_investigations = sum(1 for i in incidents_30d if i.status in ["reported", "under_investigation"])

    return {
        "safety_kpis": {
            "incidents_7d": len(incidents_7d),
            "incidents_30d": len(incidents_30d),
            "incidents_90d": len(incidents_90d),
            "critical_incidents_30d": critical_incidents,
            "open_investigations": open_investigations,
            "alcohol_violations_30d": alcohol_violations_30d,
            "operational_compliance_rate_30d": compliance_rate,
            "grounded_aviators_30d": grounded_30d,
            "rcaa_reported_incidents_30d": sum(1 for i in incidents_30d if i.rcaa_reported),
        }
    }


@router.get("/trends")
def get_safety_trends(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safety trend analysis by week."""
    if not has_permission(current_user, VIEW_SAFETY_ANALYTICS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    weekly = []
    weeks = days // 7

    for w in range(weeks - 1, -1, -1):
        wk_start = datetime.utcnow() - timedelta(days=(w + 1) * 7)
        wk_end   = datetime.utcnow() - timedelta(days=w * 7)

        incidents = db.query(SafetyIncident).filter(
            SafetyIncident.incident_date >= wk_start,
            SafetyIncident.incident_date < wk_end,
        ).all()

        alcohol_violations = db.query(AlcoholScreening).filter(
            AlcoholScreening.is_violation == True,
            AlcoholScreening.screening_date >= wk_start,
            AlcoholScreening.screening_date < wk_end,
        ).count()

        weekly.append({
            "week_start": wk_start.strftime("%Y-%m-%d"),
            "week_end": wk_end.strftime("%Y-%m-%d"),
            "total_incidents": len(incidents),
            "critical_incidents": sum(1 for i in incidents if i.severity == "critical"),
            "high_severity": sum(1 for i in incidents if i.severity == "high"),
            "alcohol_violations": alcohol_violations,
            "by_type": {
                "fatigue": sum(1 for i in incidents if i.incident_type == "fatigue"),
                "alcohol": sum(1 for i in incidents if i.incident_type == "alcohol"),
                "medical": sum(1 for i in incidents if i.incident_type == "medical"),
                "operational": sum(1 for i in incidents if i.incident_type == "operational"),
                "near_miss": sum(1 for i in incidents if i.incident_type == "near_miss"),
            },
        })

    return {"period": period, "trend": weekly}


@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def report_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Report a new safety incident."""
    if not has_permission(current_user, REPORT_SAFETY_INCIDENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    incident = SafetyIncident(
        reporter_id=current_user.id,
        involved_user_id=data.involved_user_id,
        incident_date=data.incident_date,
        incident_type=data.incident_type,
        severity=data.severity,
        title=data.title,
        description=data.description,
        location=data.location,
        flight_number=data.flight_number,
        aircraft_type=data.aircraft_type,
        phase_of_flight=data.phase_of_flight,
        is_confidential=data.is_confidential,
        status="reported",
    )
    db.add(incident)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="safety_incident_reported",
        resource_type="safety_incident",
        resource_id="new",
        action_details=f"Incident: {data.title} | Type: {data.incident_type} | Severity: {data.severity}",
        module="Safety Analytics",
        success=True,
    ))
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(
    status_filter: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    days: int = Query(30, le=365),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List safety incidents with optional filters."""
    if not has_permission(current_user, VIEW_SAFETY_ANALYTICS) and not has_permission(current_user, REPORT_SAFETY_INCIDENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.query(SafetyIncident).filter(SafetyIncident.incident_date >= cutoff)

    if status_filter:
        q = q.filter(SafetyIncident.status == status_filter)
    if severity:
        q = q.filter(SafetyIncident.severity == severity)

    # Aviators only see non-confidential incidents they reported
    if current_user.role == UserRole.AVIATOR:
        q = q.filter(SafetyIncident.reporter_id == current_user.id)

    return q.order_by(desc(SafetyIncident.incident_date)).limit(limit).all()


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update incident investigation status and findings."""
    if not has_permission(current_user, MANAGE_SAFETY_INCIDENTS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Safety Officer role required.")

    incident = db.query(SafetyIncident).filter(SafetyIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(incident, field, value)

    if data.status == "closed":
        incident.closed_at = datetime.utcnow()
        incident.investigated_by = current_user.id

    incident.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="safety_incident_updated",
        resource_type="safety_incident",
        resource_id=str(incident_id),
        action_details=f"Incident #{incident_id} updated by {current_user.full_name} → {data.status}",
        module="Safety Analytics",
        success=True,
    ))
    db.commit()
    db.refresh(incident)
    return incident
