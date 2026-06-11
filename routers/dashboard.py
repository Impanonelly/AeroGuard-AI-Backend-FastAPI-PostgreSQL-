from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from database import get_db
from models import (
    User, UserRole, FitnessAssessment, AlcoholScreening,
    SubstanceScreening, DutyPeriod, HealthRecord,
    AuditLog, Notification, AlertnessReading,
    FRMSEntry, SafetyIncident, ComplianceCheck, RiskPredictionLog,
    MedicalRecord
)
from auth.dependencies import get_current_user

router = APIRouter()

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _since(hours: int):
    return datetime.utcnow() - timedelta(hours=hours)

def _since_days(days: int):
    return datetime.utcnow() - timedelta(days=days)


# ──────────────────────────────────────────────
# UNIFIED DASHBOARD ENDPOINT (role-aware)
# ──────────────────────────────────────────────

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns role-specific dashboard KPIs.
    Each role sees only the data relevant to their responsibilities.
    """
    role = current_user.role

    if role == UserRole.ADMINISTRATOR:
        return _admin_dashboard(db)
    elif role == UserRole.SAFETY_OFFICER:
        return _safety_officer_dashboard(db)
    elif role == UserRole.SUPERVISOR:
        return _supervisor_dashboard(db, current_user)
    elif role == UserRole.MEDICAL_OFFICER:
        return _medical_officer_dashboard(db)
    elif role == UserRole.AVIATOR:
        return _aviator_dashboard(db, current_user)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role.")


def _get_active_aviators_status_counts(db: Session):
    aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).all()
    cleared = 0
    conditional = 0
    grounded = 0
    for av in aviators:
        latest = db.query(FitnessAssessment).filter(
            FitnessAssessment.user_id == av.id
        ).order_by(desc(FitnessAssessment.assessment_date)).first()
        
        status = latest.clearance_status if latest else "grounded"
        if status == "cleared":
            cleared += 1
        elif status == "conditional":
            conditional += 1
        else:
            grounded += 1
            
    return cleared, conditional, grounded


def _admin_dashboard(db: Session) -> dict:
    total_users = db.query(User).filter(User.is_active == True).count()
    total_aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).count()

    recent_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.assessment_date >= _since(24)
    ).all()
    cleared, conditional, grounded = _get_active_aviators_status_counts(db)

    active_duties = db.query(DutyPeriod).filter(DutyPeriod.status == "active").count()
    alcohol_violations_7d = db.query(AlcoholScreening).filter(
        AlcoholScreening.is_violation == True,
        AlcoholScreening.screening_date >= _since_days(7)
    ).count()

    open_incidents = db.query(SafetyIncident).filter(
        SafetyIncident.status.in_(["reported", "under_investigation"])
    ).count()

    audit_actions_24h = db.query(AuditLog).filter(
        AuditLog.timestamp >= _since(24)
    ).count()

    unread_notifications = db.query(Notification).filter(
        Notification.status == "unread"
    ).count()

    return {
        "role": "administrator",
        "kpis": {
            "total_active_users": total_users,
            "total_aviators": total_aviators,
            "active_duties": active_duties,
            "assessments_24h": len(recent_assessments),
            "cleared_24h": cleared,
            "grounded_24h": grounded,
            "compliance_rate": round((cleared / total_aviators * 100) if total_aviators else 100.0, 1),
            "alcohol_violations_7d": alcohol_violations_7d,
            "open_safety_incidents": open_incidents,
            "audit_actions_24h": audit_actions_24h,
            "unread_notifications": unread_notifications,
        }
    }


def _safety_officer_dashboard(db: Session) -> dict:
    total_aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).count()
    recent_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.assessment_date >= _since(24)
    ).all()
    cleared, conditional, grounded = _get_active_aviators_status_counts(db)

    critical_risk = db.query(RiskPredictionLog).filter(
        RiskPredictionLog.prediction_timestamp >= _since_days(7),
        RiskPredictionLog.predicted_risk_level == "CRITICAL"
    ).count()

    frms_warnings = db.query(FRMSEntry).filter(
        FRMSEntry.entry_date >= _since_days(7),
        FRMSEntry.frms_status.in_(["warning", "critical"])
    ).count()

    open_incidents = db.query(SafetyIncident).filter(
        SafetyIncident.status.in_(["reported", "under_investigation"])
    ).count()

    compliance_checks = db.query(ComplianceCheck).filter(
        ComplianceCheck.check_date >= _since_days(30)
    ).all()
    non_compliant = sum(1 for c in compliance_checks if not c.is_compliant)

    alcohol_violations_7d = db.query(AlcoholScreening).filter(
        AlcoholScreening.is_violation == True,
        AlcoholScreening.screening_date >= _since_days(7)
    ).count()

    return {
        "role": "safety_officer",
        "kpis": {
            "assessments_24h": len(recent_assessments),
            "cleared_24h": cleared,
            "grounded_24h": grounded,
            "compliance_rate": round((cleared / total_aviators * 100) if total_aviators else 100.0, 1),
            "critical_risk_predictions_7d": critical_risk,
            "frms_warnings_7d": frms_warnings,
            "open_safety_incidents": open_incidents,
            "non_compliant_checks_30d": non_compliant,
            "alcohol_violations_7d": alcohol_violations_7d,
        }
    }


def _supervisor_dashboard(db: Session, current_user: User) -> dict:
    active_duties = db.query(DutyPeriod).filter(DutyPeriod.status == "active").count()

    recent_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.assessment_date >= _since(24)
    ).all()
    cleared, conditional, grounded = _get_active_aviators_status_counts(db)

    frms_critical = db.query(FRMSEntry).filter(
        FRMSEntry.entry_date >= _since(24),
        FRMSEntry.frms_status == "critical"
    ).count()

    pending_overrides = db.query(FitnessAssessment).filter(
        FitnessAssessment.clearance_status == "conditional",
        FitnessAssessment.supervisor_override == False,
        FitnessAssessment.assessment_date >= _since(24)
    ).count()

    low_alertness = db.query(AlertnessReading).filter(
        AlertnessReading.reading_timestamp >= _since(12),
        AlertnessReading.alertness_level.in_(["low", "critical"])
    ).count()

    return {
        "role": "supervisor",
        "kpis": {
            "active_duties": active_duties,
            "assessments_24h": len(recent_assessments),
            "cleared_24h": cleared,
            "conditional_24h": conditional,
            "grounded_24h": grounded,
            "frms_critical_alerts": frms_critical,
            "pending_override_approvals": pending_overrides,
            "low_alertness_readings_12h": low_alertness,
        }
    }


def _medical_officer_dashboard(db: Session) -> dict:
    from models import MedicalRecord
    expired_medicals = db.query(MedicalRecord).filter(
        MedicalRecord.valid_until <= datetime.utcnow(),
        MedicalRecord.clearance_status == "cleared"
    ).count()

    expiring_soon = db.query(MedicalRecord).filter(
        MedicalRecord.valid_until >= datetime.utcnow(),
        MedicalRecord.valid_until <= datetime.utcnow() + timedelta(days=30),
        MedicalRecord.clearance_status == "cleared"
    ).count()

    total_medical_records = db.query(MedicalRecord).count()

    recent_health = db.query(HealthRecord).filter(
        HealthRecord.record_date >= _since_days(7)
    ).count()

    high_stress = db.query(HealthRecord).filter(
        HealthRecord.record_date >= _since_days(7),
        HealthRecord.stress_level >= 7.0
    ).count()

    substance_violations_30d = db.query(SubstanceScreening).filter(
        SubstanceScreening.is_violation == True,
        SubstanceScreening.screening_date >= _since_days(30)
    ).count()

    return {
        "role": "medical_officer",
        "kpis": {
            "total_medical_records": total_medical_records,
            "expired_medical_certificates": expired_medicals,
            "expiring_in_30_days": expiring_soon,
            "health_records_7d": recent_health,
            "high_stress_cases_7d": high_stress,
            "substance_violations_30d": substance_violations_30d,
        }
    }


def _aviator_dashboard(db: Session, current_user: User) -> dict:
    latest_assessment = db.query(FitnessAssessment).filter(
        FitnessAssessment.user_id == current_user.id
    ).order_by(desc(FitnessAssessment.assessment_date)).first()

    active_duty = db.query(DutyPeriod).filter(
        DutyPeriod.user_id == current_user.id,
        DutyPeriod.status == "active"
    ).first()

    duty_hours_7d = db.query(func.sum(DutyPeriod.duty_hours)).filter(
        DutyPeriod.user_id == current_user.id,
        DutyPeriod.duty_start >= _since_days(7),
        DutyPeriod.status == "completed"
    ).scalar() or 0.0

    unread_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status == "unread"
    ).count()

    # Assessments Submitted count
    assessments_count = db.query(FitnessAssessment).filter(
        FitnessAssessment.user_id == current_user.id
    ).count()

    # Rest deficiencies & Compliance rate
    total_completed_periods = db.query(DutyPeriod).filter(
        DutyPeriod.user_id == current_user.id,
        DutyPeriod.status == "completed"
    ).count()

    rest_violations = db.query(DutyPeriod).filter(
        DutyPeriod.user_id == current_user.id,
        DutyPeriod.rest_hours_before < 11.0
    ).count()

    rest_compliance_rate = 100
    if total_completed_periods > 0:
        rest_compliance_rate = round(((total_completed_periods - rest_violations) / total_completed_periods) * 100)

    # BAC levels (simulated pre-flight screenings)
    latest_alcohol = db.query(AlcoholScreening).filter(
        AlcoholScreening.user_id == current_user.id
    ).order_by(desc(AlcoholScreening.screening_date)).first()

    return {
        "role": "aviator",
        "kpis": {
            "clearance_status": latest_assessment.clearance_status if latest_assessment else "no_assessment",
            "fit_for_duty": latest_assessment.fit_for_duty if latest_assessment else False,
            "overall_score": latest_assessment.overall_score if latest_assessment else None,
            "active_duty": bool(active_duty),
            "duty_hours_7d": round(duty_hours_7d, 1),
            "current_alertness_score": latest_assessment.fatigue_score if latest_assessment else 90.0,
            "alertness_level": latest_assessment.alertness_level if latest_assessment else "high",
            "current_risk_level": latest_assessment.risk_level if latest_assessment else "LOW",
            "unread_notifications": unread_notifications,
            "assessments_count": assessments_count,
            "rest_deficiencies": rest_violations,
            "rest_compliance_rate": rest_compliance_rate,
            "sleep_hours": latest_assessment.sleep_hours_last_night if (latest_assessment and latest_assessment.sleep_hours_last_night is not None) else 8.2,
            "stress_level": latest_assessment.stress_level if (latest_assessment and latest_assessment.stress_level is not None) else 3.0,
            "fatigue_level": latest_assessment.fatigue_level if (latest_assessment and latest_assessment.fatigue_level is not None) else 2.0,
            "workload_perception": latest_assessment.workload_perception if (latest_assessment and latest_assessment.workload_perception is not None) else 3.0,
            "duty_hours_today": latest_assessment.duty_hours_today if (latest_assessment and latest_assessment.duty_hours_today is not None) else 4.0,
            "bac_level": latest_alcohol.bac_level if (latest_alcohol and latest_alcohol.bac_level is not None) else 0.0,
        }
    }


# ── Aviator Notifications & Alerts Redesign Endpoints ─────────────────────

@router.get("/aviator/flight")
def get_aviator_flight(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if they have submitted an assessment today
    today_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.user_id == current_user.id,
        FitnessAssessment.assessment_date >= today_start
    ).all()
    
    screening_completed = len(today_assessments) > 0
    
    # Check alcohol screening from latest AlcoholScreening today
    latest_alcohol = db.query(AlcoholScreening).filter(
        AlcoholScreening.user_id == current_user.id,
        AlcoholScreening.screening_date >= today_start
    ).order_by(desc(AlcoholScreening.screening_date)).first()
    
    alcohol_completed = latest_alcohol is not None and latest_alcohol.bac_level == 0.0
    
    # Check medical certificate status (if expired)
    latest_medical = db.query(MedicalRecord).filter(
        MedicalRecord.user_id == current_user.id
    ).order_by(desc(MedicalRecord.record_date)).first()
    
    is_medical_expired = False
    if latest_medical:
        if latest_medical.valid_until and latest_medical.valid_until < datetime.utcnow():
            is_medical_expired = True
    else:
        is_medical_expired = True # If no medical certificate, treat as expired/missing
        
    clearance_status = "Cleared for Duty"
    latest_fit = db.query(FitnessAssessment).filter(
        FitnessAssessment.user_id == current_user.id
    ).order_by(desc(FitnessAssessment.assessment_date)).first()
    if latest_fit:
        clearance_status = latest_fit.clearance_status
    elif is_medical_expired:
        clearance_status = "Not Cleared"
        
    blocking_requirements = []
    if not screening_completed:
        blocking_requirements.append("Pre-Flight Clearance Declaration Pending")
    if not alcohol_completed:
        blocking_requirements.append("Breathalyzer Alcohol Screening Pending")
        
    if is_medical_expired:
        blocking_requirements.append("Class 1 Medical Certificate Renewal Overdue")
        clearance_status = "Not Cleared (Lockout)"
    elif not screening_completed or not alcohol_completed:
        clearance_status = "Conditional Clearance"
        
    # Roster mapping based on user email/ID
    if current_user.email == "grace@demo.com" or current_user.id == 13: # Grace Mutesi (aviator)
        flight_number = "AW-102"
        aircraft = "Boeing 737-800"
        route = "KGL ➔ NBO (Kigali to Nairobi)"
        departure = "Today, 15:30 PM (In 2h 15m)"
    elif current_user.email == "patrick@demo.com" or current_user.id == 12: # Patrick Mugisha
        flight_number = "AW-304"
        aircraft = "Airbus A320"
        route = "KGL ➔ JNB (Kigali to Johannesburg)"
        departure = "Today, 17:45 PM (In 4h 30m)"
    else:
        flight_number = "AW-999"
        aircraft = "Cessna Grand Caravan"
        route = "KGL ➔ GYI (Kigali to Gisenyi)"
        departure = "Tomorrow, 09:00 AM"
        
    return {
        "flight_number": flight_number,
        "aircraft": aircraft,
        "route": route,
        "departure_time": departure,
        "clearance_status": clearance_status,
        "screening_completed": screening_completed,
        "alcohol_completed": alcohol_completed,
        "medical_valid": not is_medical_expired,
        "blocking_requirements": blocking_requirements
    }


@router.get("/aviator/certifications")
def get_aviator_certifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest_medical = db.query(MedicalRecord).filter(
        MedicalRecord.user_id == current_user.id
    ).order_by(desc(MedicalRecord.record_date)).first()
    
    med_days = -1
    if latest_medical and latest_medical.valid_until:
        med_days = (latest_medical.valid_until - datetime.utcnow()).days
        
    if current_user.email == "grace@demo.com" or current_user.id == 13: # Grace (expired medical certificate)
        return {
            "medical_certificate": {"name": "Class 1 Medical Certificate", "days_remaining": med_days if med_days < 0 else -1, "status": "EXPIRED", "required_action": "Schedule FAA/RCAA Aviation Medical Exam immediately."},
            "pilot_license": {"name": "ATPL Pilot License", "days_remaining": 145, "status": "VALID", "required_action": "None"},
            "type_rating": {"name": "B737-800 Type Rating", "days_remaining": 82, "status": "VALID", "required_action": "None"},
            "crew_training": {"name": "CRM Crew Resource Management", "days_remaining": 12, "status": "WARNING", "required_action": "Enroll in CRM refresher module."},
            "simulator_check": {"name": "B737 Flight Simulator Check", "days_remaining": 4, "status": "WARNING", "required_action": "Simulator check scheduled for June 6th."}
        }
    else: # Others
        return {
            "medical_certificate": {
                "name": "Class 1 Medical Certificate", 
                "days_remaining": max(0, med_days) if (latest_medical and med_days >= 0) else 74, 
                "status": "VALID" if (latest_medical and med_days >= 0) else "VALID", 
                "required_action": "None"
            },
            "pilot_license": {"name": "CPL Pilot License", "days_remaining": 220, "status": "VALID", "required_action": "None"},
            "type_rating": {"name": "A320 Type Rating", "days_remaining": 15, "status": "WARNING", "required_action": "Type rating recurrent training due in 15 days."},
            "crew_training": {"name": "CRM Crew Resource Management", "days_remaining": 180, "status": "VALID", "required_action": "None"},
            "simulator_check": {"name": "A320 Flight Simulator Check", "days_remaining": 65, "status": "VALID", "required_action": "None"}
        }


@router.get("/alerts")
def get_dashboard_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).all()
    
    if not notifications:
        # Generate some mock notifications in the database for the user so it's populated
        mock_data = []
        if current_user.email == "grace@demo.com" or current_user.id == 13:
            mock_data = [
                {
                    "title": "Class 1 Medical Certificate Overdue",
                    "message": "Your ICAO Class 1 Medical Certificate has officially expired. RCAA Regulations require immediate grounding until an aviation surgeon check is completed.",
                    "notification_type": "medical",
                    "priority": "critical",
                    "status": "unread"
                },
                {
                    "title": "Fatigue Threshold Alert",
                    "message": "Dynamic readiness monitoring has flagged elevated fatigue risk due to irregular sleep cycles logged this week.",
                    "notification_type": "fatigue",
                    "priority": "high",
                    "status": "unread"
                },
                {
                    "title": "Log Pattern Consistency Notice",
                    "message": "Safety management system flagged a pattern consistency anomaly in the last 4 pre-flight readiness declarations.",
                    "notification_type": "inconsistency",
                    "priority": "medium",
                    "status": "unread"
                },
                {
                    "title": "Flight Duty Buffer Verified",
                    "message": "11.5 hours rest period buffer before flight AW-102 verified successfully.",
                    "notification_type": "duty",
                    "priority": "low",
                    "status": "read"
                }
            ]
        else:
            mock_data = [
                {
                    "title": "Class 1 Medical Expiration Watch",
                    "message": "Your Class 1 Medical Certificate expires in 74 days. No immediate action required, but scheduling a check-in is recommended.",
                    "notification_type": "medical",
                    "priority": "medium",
                    "status": "unread"
                },
                {
                    "title": "CRM Recurrent Training Session",
                    "message": "CRM Refresher training scheduled for June 18, 2026. Please verify attendance details.",
                    "notification_type": "training",
                    "priority": "medium",
                    "status": "unread"
                },
                {
                    "title": "Flight Duty Buffer Verified",
                    "message": "11.5 hours rest period buffer before flight AW-304 verified successfully.",
                    "notification_type": "duty",
                    "priority": "low",
                    "status": "read"
                }
            ]
            
        for md in mock_data:
            notif = Notification(
                user_id=current_user.id,
                title=md["title"],
                message=md["message"],
                notification_type=md["notification_type"],
                priority=md["priority"],
                status=md["status"],
                created_at=datetime.utcnow() - timedelta(hours=mock_data.index(md) * 2)
            )
            db.add(notif)
        db.commit()
        
        notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(desc(Notification.created_at)).all()
        
    result = []
    for n in notifications:
        diff = datetime.utcnow() - n.created_at
        if diff.days > 0:
            time_ago = f"{diff.days} days ago"
        elif diff.seconds // 3600 > 0:
            time_ago = f"{diff.seconds // 3600} hours ago"
        elif diff.seconds // 60 > 0:
            time_ago = f"{diff.seconds // 60} mins ago"
        else:
            time_ago = "Just now"
            
        ui_type = n.notification_type
        if ui_type in ["critical", "alert"]:
            ui_type = "fatigue"
            
        result.append({
            "id": n.id,
            "user_id": n.user_id,
            "title": n.title,
            "description": n.message,
            "time_ago": time_ago,
            "type": ui_type,
            "is_read": n.status != "unread"
        })
    return result


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(
        Notification.id == alert_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this alert")
        
    notification.status = "read"
    notification.read_at = datetime.utcnow()
    
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="alert_acknowledged",
        resource_type="notification",
        resource_id=str(alert_id),
        action_details=f"Aviator {current_user.full_name} acknowledged alert: '{notification.title}'.",
        module="Notifications",
        success=True
    ))
    db.commit()
    return {"status": "success"}
