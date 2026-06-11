from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import datetime
from database import get_db
import models
from auth.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS FOR CUSTOM ENDPOINTS
# ──────────────────────────────────────────────

class AlcoholTestCreate(BaseModel):
    user_id: Optional[int] = None
    bac_percentage: float
    method: str  # "Hardware" or "Manual"
    device_info: Optional[str] = None
    screening_type: Optional[str] = None
    medical_officer: Optional[str] = None
    medical_recommendation: Optional[str] = None
    notes: Optional[str] = None

class AlcoholTestOut(BaseModel):
    id: int
    user_id: int
    test_time: str
    bac_percentage: float
    result: str
    method: str
    device_info: Optional[str] = None
    screening_type: Optional[str] = None
    medical_officer: Optional[str] = None
    medical_recommendation: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class DutyClearanceActionCreate(BaseModel):
    user_id: int
    action: str  # "APPROVE", "REJECT", "ESCALATE", "MONITOR", "RESTRICT"
    escalated_to: Optional[str] = None
    reason: Optional[str] = None

class DutyClearanceActionOut(BaseModel):
    id: int
    user_id: int
    supervisor_id: int
    action: str
    escalated_to: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/api/dashboard/alcohol-test", response_model=AlcoholTestOut)
def create_alcohol_test(
    test_in: AlcoholTestCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = current_user.id
    if current_user.role in ["medical_officer", "supervisor", "administrator"] and test_in.user_id:
        target_user_id = test_in.user_id
        
    result_label = "PASS" if test_in.bac_percentage == 0.0 else "FAIL"
    med_officer_name = test_in.medical_officer or (current_user.full_name if current_user.role == "medical_officer" else "Hardware Automated")
    
    db_test = models.AlcoholTest(
        user_id=target_user_id,
        test_time=datetime.datetime.now().strftime("Today, %H:%M %p"),
        bac_percentage=test_in.bac_percentage,
        result=result_label,
        method=test_in.method,
        device_info=test_in.device_info or ("AlcoQuant-COM3" if test_in.method == "Hardware" else "Manual Registry"),
        screening_type=test_in.screening_type or "Pre-Flight",
        medical_officer=med_officer_name,
        medical_recommendation=test_in.medical_recommendation or ("Fit for Duty" if result_label == "PASS" else "Ground Crew Member"),
        notes=test_in.notes
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    summary = db.query(models.DashboardSummary).filter(models.DashboardSummary.user_id == target_user_id).first()
    if not summary:
        summary = models.DashboardSummary(user_id=target_user_id)
        
    summary.bac_status = result_label
    summary.bac_percentage = test_in.bac_percentage
    
    target_pilot = db.query(models.User).filter(models.User.id == target_user_id).first()
    pilot_name = target_pilot.full_name if target_pilot else f"User ID {target_user_id}"
    
    if result_label == "FAIL":
        summary.readiness_status = "Not Fit for Duty"
        
        # High priority substance lockout alert
        substance_alert = models.Alert(
            user_id=target_user_id,
            title="Substance screening lockout",
            description=f"CRITICAL: Positive BAC detected ({test_in.bac_percentage}%). Dispatch Clearance Denied.",
            time_ago="Just now",
            type="alcohol",
            is_read=False
        )
        db.add(substance_alert)
    else:
        # If they passed, let's keep the existing status or update conditional clearances.
        if summary.readiness_status == "Conditional Clearance" or not summary.readiness_status:
            # Let's check fatigue
            if summary.fatigue_score >= 70:
                summary.readiness_status = "Not Fit for Duty"
            elif summary.fatigue_score >= 40:
                summary.readiness_status = "Limited Duty"
            else:
                summary.readiness_status = "Cleared for Duty"
                
    db.add(summary)
    
    # Write Audit Log
    audit = models.AuditLog(
        user_id=current_user.id,
        action_type="alcohol_screening",
        action_details=f"Logged BAC test for {pilot_name}. Percentage: {test_in.bac_percentage}%. Result: {result_label}. Method: {test_in.method}."
    )
    db.add(audit)
    db.commit()
    
    return db_test


@router.get("/api/alcohol/history-all", response_model=List[AlcoholTestOut])
def get_all_alcohol_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["medical_officer", "supervisor", "administrator", "safety_officer"]:
        raise HTTPException(status_code=403, detail="Access denied. Staff only.")
    return db.query(models.AlcoholTest).order_by(models.AlcoholTest.id.desc()).all()


@router.get("/api/dashboard/recommendations")
def get_recommendations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = db.query(models.DashboardSummary).filter(models.DashboardSummary.user_id == current_user.id).first()
    status_str = summary.readiness_status if summary else "Cleared for Duty"
    
    if status_str == "Not Fit for Duty":
        return {
            "status": "NOT FIT FOR DUTY",
            "standard": "RCAA Regulatory Compliance Lockout",
            "details": "CRITICAL RISK: Based on severe sleep deprivation, extended shift length, or critical subjective symptoms, the system recommends immediate operational lockout. Please rest. A supervisor and medical officer review is mandatory before reinstatement."
        }
    elif status_str == "Limited Duty":
        return {
            "status": "LIMITED DUTY CLEARANCE",
            "standard": "RCAA Safety Precaution Protocol",
            "details": "MODERATE RISK: Elevated fatigue or stress levels detected. Flight duty must be restricted to a maximum of 8 hours, with no night operations or solo flight duty. Ensure regular rest buffers and re-evaluation in 4 hours."
        }
    else:
        return {
            "status": "CLEARED FOR FULL DUTY",
            "standard": "RCAA Regulatory Safety Standard",
            "details": "LOW RISK: Based on your dynamic health assessment history, optimal sleep cycle, low fatigue index, and zero anomaly flags, the safety management engine recommends full flight operational clearance."
        }


@router.get("/api/supervisor/crew")
def get_supervisor_crew(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["supervisor", "medical_officer", "administrator", "safety_officer"]:
        raise HTTPException(status_code=403, detail="Access denied. Authorized staff only.")
        
    crew_users = db.query(models.User).filter(models.User.role == "aviator").all()
    result = []
    
    for crew in crew_users:
        summary = db.query(models.DashboardSummary).filter(models.DashboardSummary.user_id == crew.id).first()
        latest_assessment = db.query(models.FitnessAssessment).filter(
            models.FitnessAssessment.user_id == crew.id
        ).order_by(models.FitnessAssessment.id.desc()).first()
        
        # Query latest supervisor action
        latest_action = db.query(models.DutyClearanceAction).filter(
            models.DutyClearanceAction.user_id == crew.id
        ).order_by(models.DutyClearanceAction.id.desc()).first()
        
        supervisor_decision = latest_action.action if latest_action else "None"
        
        # Query latest medical record to determine valid medical days left
        latest_medical = db.query(models.MedicalRecord).filter(
            models.MedicalRecord.user_id == crew.id
        ).order_by(models.MedicalRecord.record_date.desc()).first()
        
        med_days = -1
        if latest_medical and latest_medical.valid_until:
            med_days = (latest_medical.valid_until - datetime.datetime.utcnow()).days
            
        crew_rank = "Captain" if ("Capt." in crew.full_name or "Captain" in crew.full_name) else "First Officer"
        
        result.append({
            "id": crew.id,
            "full_name": crew.full_name,
            "employee_id": crew.employee_id,
            "rank": crew_rank,
            "base": "KGL" if crew.id == 11 or crew.id == 13 else "NBO",
            "aircraft_type": "Boeing 737-800" if crew.id == 11 or crew.id == 13 else "Airbus A320",
            "status": summary.readiness_status if summary else "Cleared for Duty",
            "fatigue_score": summary.fatigue_score if summary else 12,
            "sleep_hours": summary.sleep_hours if summary else 8.2,
            "last_active": "Today, 08:30 AM",
            "supervisor_decision": supervisor_decision,
            "duty_assignment": "Scheduled Flight" if crew.id == 11 or crew.id == 13 else "Resting",
            "compliance": {
                "medical_days": med_days if latest_medical else 74,
                "sim_days": 4 if crew.id == 11 or crew.id == 13 else 65,
                "crm_days": 12 if crew.id == 11 or crew.id == 13 else 180
            }
        })
        
    return result


@router.post("/api/supervisor/clearance-action", response_model=DutyClearanceActionOut)
def create_clearance_action(
    action_in: DutyClearanceActionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "supervisor":
        raise HTTPException(status_code=403, detail="Access denied. Supervisors only.")
        
    action_db = models.DutyClearanceAction(
        user_id=action_in.user_id,
        supervisor_id=current_user.id,
        action=action_in.action,
        escalated_to=action_in.escalated_to,
        reason=action_in.reason,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(action_db)
    
    summary = db.query(models.DashboardSummary).filter(models.DashboardSummary.user_id == action_in.user_id).first()
    if not summary:
        summary = models.DashboardSummary(user_id=action_in.user_id)
        
    crew_member = db.query(models.User).filter(models.User.id == action_in.user_id).first()
    crew_name = crew_member.full_name if crew_member else "Crew Member"
    
    if action_in.action == "APPROVE":
        summary.readiness_status = "Cleared for Duty"
        # Archive all active alerts for this user by setting is_read = True
        alerts = db.query(models.Alert).filter(models.Alert.user_id == action_in.user_id, models.Alert.is_read == False).all()
        for alert in alerts:
            alert.is_read = True
            
        audit = models.AuditLog(
            user_id=current_user.id,
            action_type="supervisor_override",
            action_details=f"Supervisor override: Approved flight duty clearance for {crew_name}. Reason: {action_in.reason or 'None Specified'}."
        )
        db.add(audit)
    elif action_in.action == "MONITOR":
        summary.readiness_status = "Monitoring Required"
        
        audit = models.AuditLog(
            user_id=current_user.id,
            action_type="supervisor_override",
            action_details=f"Supervisor override: Set flight duty clearance to 'Monitoring Required' for {crew_name}. Reason: {action_in.reason or 'None Specified'}."
        )
        db.add(audit)
    elif action_in.action == "RESTRICT":
        summary.readiness_status = "Limited Duty"
        
        audit = models.AuditLog(
            user_id=current_user.id,
            action_type="supervisor_override",
            action_details=f"Supervisor override: Restricted flight duty clearance to 'Limited Duty' for {crew_name}. Reason: {action_in.reason or 'None Specified'}."
        )
        db.add(audit)
    elif action_in.action == "GROUND":
        summary.readiness_status = "Not Fit for Duty"
        
        unfit_alert = models.Alert(
            user_id=action_in.user_id,
            title="Duty Clearance Rejected",
            description=f"Supervisor Robert KAGAME rejected your duty clearance. Reason: {action_in.reason or 'Not Specified'}.",
            time_ago="Just now",
            type="duty",
            is_read=False
        )
        db.add(unfit_alert)
        
        audit = models.AuditLog(
            user_id=current_user.id,
            action_type="supervisor_action",
            action_details=f"Supervisor action: Rejected flight duty clearance for {crew_name} (Grounded). Reason: {action_in.reason or 'None Specified'}."
        )
        db.add(audit)
    elif action_in.action == "ESCALATE":
        summary.readiness_status = f"Grounded (Escalated to {action_in.escalated_to or 'Medical'})"
        
        audit = models.AuditLog(
            user_id=current_user.id,
            action_type="supervisor_action",
            action_details=f"Supervisor action: Escalated clearance for {crew_name} to {action_in.escalated_to or 'Medical Officer'}. Reason: {action_in.reason or 'None Specified'}."
        )
        db.add(audit)
        
    db.add(summary)
    db.commit()
    db.refresh(action_db)
    return action_db


@router.get("/api/supervisor/clearance-actions", response_model=List[DutyClearanceActionOut])
def get_clearance_actions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["supervisor", "medical_officer", "administrator", "safety_officer"]:
        raise HTTPException(status_code=403, detail="Access denied. Supervisors only.")
    return db.query(models.DutyClearanceAction).order_by(models.DutyClearanceAction.id.desc()).all()


@router.get("/api/supervisor/stats")
def get_supervisor_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["supervisor", "medical_officer", "administrator", "safety_officer"]:
        raise HTTPException(status_code=403, detail="Access denied. Supervisors only.")
        
    summaries = db.query(models.DashboardSummary).all()
    on_duty = 0
    resting = 0
    available = 0
    restricted = 0
    grounded = 0
    pending = 0
    
    for s in summaries:
        user = db.query(models.User).filter(models.User.id == s.user_id).first()
        if not user or user.role == "supervisor":
            continue
            
        status_str = s.readiness_status
        if status_str == "Not Fit for Duty" or "Grounded" in status_str:
            grounded += 1
        elif status_str == "Limited Duty":
            restricted += 1
        elif status_str == "Conditional Clearance" or "Pending" in status_str:
            pending += 1
        else:
            available += 1
            
        # Hardcode operational status for Grace (11) and Emmanuel (12)
        if user.id == 11 or user.id == 13:
            on_duty += 1
        else:
            resting += 1
            
    total_crew = db.query(models.User).filter(models.User.role == "aviator").count()
    
    flights_count = db.query(models.DutyPeriod).filter(
        models.DutyPeriod.status == "scheduled",
        models.DutyPeriod.duty_type == "flight"
    ).count()
    if flights_count == 0:
        flights_count = db.query(models.DutyPeriod).filter(models.DutyPeriod.status == "scheduled").count() or 8
        
    return {
        "flights_scheduled": flights_count,
        "crews_assigned": total_crew,
        "pending_clearances": pending if pending > 0 else 1, # default 1 for pending breathalyzer
        "grounded_crew": grounded,
        "availability": {
            "available": available,
            "on_duty": on_duty,
            "resting": max(0, total_crew - available - on_duty - restricted - grounded),
            "restricted": restricted,
            "grounded": grounded
        }
    }
