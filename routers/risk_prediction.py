from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import RiskPredictionLog, HealthRecord, AlertnessReading, DutyPeriod, FRMSEntry, User, AuditLog, Notification
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_RISK_PREDICTIONS, VIEW_CREW_DATA, VIEW_ALL_PERSONNEL
from ai_engine.model import predict_risk

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class RiskAnalysisRequest(BaseModel):
    user_id: int
    sleep_hours: float = Field(..., ge=0, le=24)
    duty_hours: float = Field(..., ge=0, le=24)
    stress_level: float = Field(..., ge=0, le=10)
    alertness_score: Optional[float] = Field(None, ge=0, le=100)
    heart_rate: Optional[float] = None
    reaction_time_ms: Optional[float] = None

class RiskPredictionResponse(BaseModel):
    id: int
    user_id: int
    prediction_timestamp: datetime
    predicted_risk_level: str
    risk_score: float
    confidence_score: Optional[float]
    model_version: str
    contributing_factors: Optional[str]
    recommendations: Optional[str]
    alert_generated: bool
    action_taken: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _build_recommendations(risk_level: str, factors: list) -> str:
    base = {
        "LOW":      "Continue normal operations. Maintain rest schedule.",
        "MEDIUM":   "Monitor closely. Reduce non-essential duties. Ensure 8h rest before next flight.",
        "HIGH":     "Recommend grounding from flight duties. Mandatory rest period. Supervisor review required.",
        "CRITICAL": "IMMEDIATE GROUNDING required. Medical evaluation before return to duty.",
    }
    recs = [base.get(risk_level, "Review operational status.")]
    if "sleep_debt" in factors:
        recs.append("Address sleep deficit — minimum 8h uninterrupted sleep required.")
    if "high_stress" in factors:
        recs.append("Stress intervention recommended — consider counseling or workload reduction.")
    if "high_duty_hours" in factors:
        recs.append("Duty hours approaching regulatory limit — schedule mandatory rest.")
    if "low_alertness" in factors:
        recs.append("Alertness below safe threshold — cognitive performance test recommended.")
    return " | ".join(recs)

def _identify_factors(sleep: float, duty: float, stress: float, alertness: Optional[float]) -> list:
    factors = []
    if sleep < 6:
        factors.append("sleep_debt")
    if duty > 10:
        factors.append("high_duty_hours")
    if stress >= 7:
        factors.append("high_stress")
    if alertness is not None and alertness < 60:
        factors.append("low_alertness")
    return factors

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/analyze", response_model=RiskPredictionResponse, status_code=status.HTTP_201_CREATED)
def analyze_risk(
    data: RiskAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit operational data for AI risk analysis.
    Calls the trained Scikit-Learn fatigue model and persists the prediction.
    AI assists — does NOT replace human decision-making.
    """
    if not has_permission(current_user, VIEW_RISK_PREDICTIONS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    # Call AI engine
    try:
        ai_result = predict_risk(
            sleep_hours=data.sleep_hours,
            duty_hours=data.duty_hours,
            stress_level=data.stress_level,
        )
        risk_label = ai_result.get("risk_level", "MEDIUM")
        risk_score = ai_result.get("risk_score", 50.0)
        confidence = ai_result.get("confidence", 85.0)
    except Exception:
        # Fallback rule-based scoring if AI engine unavailable
        total = (data.sleep_hours / 8 * 40) + ((10 - data.stress_level) / 10 * 30) + ((24 - data.duty_hours) / 24 * 30)
        risk_score = round(100 - total, 1)
        confidence = 75.0
        if risk_score < 25:
            risk_label = "LOW"
        elif risk_score < 50:
            risk_label = "MEDIUM"
        elif risk_score < 75:
            risk_label = "HIGH"
        else:
            risk_label = "CRITICAL"

    factors = _identify_factors(data.sleep_hours, data.duty_hours, data.stress_level, data.alertness_score)
    recommendations = _build_recommendations(risk_label, factors)
    alert_generated = risk_label in ["HIGH", "CRITICAL"]

    log = RiskPredictionLog(
        user_id=data.user_id,
        sleep_hours_input=data.sleep_hours,
        duty_hours_input=data.duty_hours,
        stress_level_input=data.stress_level,
        alertness_score_input=data.alertness_score,
        heart_rate_input=data.heart_rate,
        reaction_time_input=data.reaction_time_ms,
        predicted_risk_level=risk_label,
        risk_score=risk_score,
        confidence_score=confidence,
        contributing_factors=str(factors),
        recommendations=recommendations,
        alert_generated=alert_generated,
        action_taken="none",
    )
    db.add(log)

    if alert_generated:
        db.add(Notification(
            user_id=data.user_id,
            title=f"🔴 {risk_label} Risk Detected",
            message=f"AI risk analysis: {risk_label} risk (score: {risk_score:.0f}/100). {recommendations[:120]}...",
            notification_type="alert",
            priority="critical" if risk_label == "CRITICAL" else "high",
            action_required=True,
        ))

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="risk_prediction_generated",
        resource_type="risk_prediction",
        resource_id=str(data.user_id),
        action_details=f"AI Risk: {risk_label} | Score: {risk_score} | Confidence: {confidence}%",
        module="Risk Prediction",
        success=True,
    ))
    db.commit()
    db.refresh(log)
    return log


@router.get("/predict/{user_id}")
def predict_user_risk(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Auto-predict risk from latest available data for a user.
    Pulls most recent health record + duty hours automatically.
    """
    if not has_permission(current_user, VIEW_RISK_PREDICTIONS) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    latest_health = db.query(HealthRecord).filter(
        HealthRecord.user_id == user_id
    ).order_by(desc(HealthRecord.record_date)).first()

    recent_duty = db.query(DutyPeriod).filter(
        DutyPeriod.user_id == user_id,
        DutyPeriod.duty_start >= datetime.utcnow() - timedelta(days=1),
    ).all()
    total_duty_hours = sum(d.duty_hours or 0 for d in recent_duty)

    sleep_hours = latest_health.sleep_hours if latest_health else 7.0
    stress_level = latest_health.stress_level if latest_health else 3.0
    alertness = latest_health.alertness_score if latest_health else 75.0

    factors = _identify_factors(sleep_hours, total_duty_hours, stress_level, alertness)

    try:
        ai_result = predict_risk(sleep_hours=sleep_hours, duty_hours=total_duty_hours, stress_level=stress_level)
        risk_label = ai_result.get("risk_level", "LOW")
        risk_score = ai_result.get("risk_score", 20.0)
        confidence = ai_result.get("confidence", 85.0)
    except Exception:
        risk_score = min(100, (10 - sleep_hours) * 5 + stress_level * 5 + total_duty_hours * 2)
        if risk_score < 25:
            risk_label = "LOW"
        elif risk_score < 50:
            risk_label = "MEDIUM"
        elif risk_score < 75:
            risk_label = "HIGH"
        else:
            risk_label = "CRITICAL"
        confidence = 75.0

    return {
        "user_id": user_id,
        "predicted_risk_level": risk_label,
        "risk_score": round(risk_score, 1),
        "confidence_score": confidence,
        "inputs_used": {
            "sleep_hours": sleep_hours,
            "duty_hours_24h": round(total_duty_hours, 1),
            "stress_level": stress_level,
            "alertness_score": alertness,
        },
        "contributing_factors": factors,
        "recommendations": _build_recommendations(risk_label, factors),
        "ai_note": "This is an AI-assisted prediction. Final decisions must be made by qualified personnel.",
    }


@router.get("/history/{user_id}", response_model=List[RiskPredictionResponse])
def get_risk_history(
    user_id: int,
    days: int = Query(30, le=365),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Historical risk predictions for a user."""
    if not has_permission(current_user, VIEW_RISK_PREDICTIONS) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(RiskPredictionLog)
        .filter(RiskPredictionLog.user_id == user_id, RiskPredictionLog.prediction_timestamp >= cutoff)
        .order_by(desc(RiskPredictionLog.prediction_timestamp))
        .limit(limit)
        .all()
    )


@router.get("/fleet-overview")
def get_fleet_risk_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fleet-wide risk distribution (Supervisor / Safety Officer / Admin)."""
    if not has_permission(current_user, VIEW_CREW_DATA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(hours=24)
    predictions = db.query(RiskPredictionLog).filter(
        RiskPredictionLog.prediction_timestamp >= cutoff
    ).all()

    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for p in predictions:
        dist[p.predicted_risk_level] = dist.get(p.predicted_risk_level, 0) + 1

    avg_score = round(sum(p.risk_score for p in predictions) / len(predictions), 1) if predictions else 0.0
    alerts_generated = sum(1 for p in predictions if p.alert_generated)

    return {
        "period_hours": 24,
        "total_predictions": len(predictions),
        "average_risk_score": avg_score,
        "distribution": dist,
        "alerts_generated": alerts_generated,
        "fleet_risk_status": "CRITICAL" if dist["CRITICAL"] > 0 else "HIGH" if dist["HIGH"] > 2 else "NORMAL",
    }
