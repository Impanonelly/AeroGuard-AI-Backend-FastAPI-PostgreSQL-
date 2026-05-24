from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from database import get_db
from models import (
    User, UserRole, FitnessAssessment, AlcoholScreening,
    SubstanceScreening, DutyPeriod, HealthRecord,
    AuditLog, Notification, AlertnessReading,
    FRMSEntry, SafetyIncident, ComplianceCheck, RiskPredictionLog
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


def _admin_dashboard(db: Session) -> dict:
    total_users = db.query(User).filter(User.is_active == True).count()
    total_aviators = db.query(User).filter(User.role == UserRole.AVIATOR, User.is_active == True).count()

    recent_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.assessment_date >= _since(24)
    ).all()
    cleared = sum(1 for a in recent_assessments if a.clearance_status == "cleared")
    grounded = sum(1 for a in recent_assessments if a.clearance_status == "grounded")

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
            "compliance_rate": round((cleared / len(recent_assessments) * 100) if recent_assessments else 100.0, 1),
            "alcohol_violations_7d": alcohol_violations_7d,
            "open_safety_incidents": open_incidents,
            "audit_actions_24h": audit_actions_24h,
            "unread_notifications": unread_notifications,
        }
    }


def _safety_officer_dashboard(db: Session) -> dict:
    recent_assessments = db.query(FitnessAssessment).filter(
        FitnessAssessment.assessment_date >= _since(24)
    ).all()
    cleared = sum(1 for a in recent_assessments if a.clearance_status == "cleared")
    grounded = sum(1 for a in recent_assessments if a.clearance_status == "grounded")

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
            "compliance_rate": round((cleared / len(recent_assessments) * 100) if recent_assessments else 100.0, 1),
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
    cleared = sum(1 for a in recent_assessments if a.clearance_status == "cleared")
    grounded = sum(1 for a in recent_assessments if a.clearance_status == "grounded")
    conditional = sum(1 for a in recent_assessments if a.clearance_status == "conditional")

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

    latest_alertness = db.query(AlertnessReading).filter(
        AlertnessReading.user_id == current_user.id
    ).order_by(desc(AlertnessReading.reading_timestamp)).first()

    latest_risk = db.query(RiskPredictionLog).filter(
        RiskPredictionLog.user_id == current_user.id
    ).order_by(desc(RiskPredictionLog.prediction_timestamp)).first()

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

    # Health Vitals (sleep, heart rate, fatigue)
    latest_health = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id
    ).order_by(desc(HealthRecord.record_date)).first()

    # BAC levels
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
            "current_alertness_score": latest_alertness.alertness_score if latest_alertness else None,
            "alertness_level": latest_alertness.alertness_level if latest_alertness else "unknown",
            "current_risk_level": latest_risk.predicted_risk_level if latest_risk else "unknown",
            "unread_notifications": unread_notifications,
            "assessments_count": assessments_count,
            "rest_deficiencies": rest_violations,
            "rest_compliance_rate": rest_compliance_rate,
            "sleep_hours": latest_health.sleep_hours if (latest_health and latest_health.sleep_hours is not None) else 8.2,
            "resting_heart_rate": latest_health.heart_rate if (latest_health and latest_health.heart_rate is not None) else 64.0,
            "fatigue_score": latest_health.fatigue_score if (latest_health and latest_health.fatigue_score is not None) else 12.0,
            "bac_level": latest_alcohol.bac_level if (latest_alcohol and latest_alcohol.bac_level is not None) else 0.0,
        }
    }
