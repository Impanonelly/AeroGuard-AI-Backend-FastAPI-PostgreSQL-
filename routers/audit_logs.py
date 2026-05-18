from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_db
from models import AuditLog, User
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_AUDIT_LOGS
import csv, io
from fastapi.responses import StreamingResponse

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    timestamp: datetime
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    action_details: Optional[str]
    module: Optional[str]
    ip_address: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    module: Optional[str] = Query(None, description="Filter by module"),
    days: int = Query(7, le=365, description="Logs from last N days"),
    limit: int = Query(100, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated audit log viewer. Administrator and Safety Officer only."""
    if not has_permission(current_user, VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Audit logs are restricted.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff)

    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action_type:
        q = q.filter(AuditLog.action_type == action_type)
    if module:
        q = q.filter(AuditLog.module == module)

    total = q.count()
    logs = q.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return logs


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
def get_user_audit_logs(
    user_id: int,
    days: int = Query(30, le=365),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs for a specific user."""
    if not has_permission(current_user, VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id, AuditLog.timestamp >= cutoff)
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
        .all()
    )


@router.get("/summary")
def get_audit_summary(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Audit log summary statistics."""
    if not has_permission(current_user, VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff).all()

    # Action type breakdown
    action_counts: dict = {}
    module_counts: dict = {}
    for log in logs:
        action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
        if log.module:
            module_counts[log.module] = module_counts.get(log.module, 0) + 1

    failed = sum(1 for l in logs if not l.success)

    return {
        "period_days": days,
        "total_events": len(logs),
        "failed_events": failed,
        "success_rate": round(((len(logs) - failed) / len(logs) * 100) if logs else 100.0, 1),
        "top_actions": dict(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        "by_module": module_counts,
    }


@router.get("/export")
def export_audit_logs(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export audit logs as CSV. Administrator only."""
    if not has_permission(current_user, VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff).order_by(desc(AuditLog.timestamp)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "User ID", "Action Type", "Resource", "Resource ID", "Module", "Details", "Success", "IP Address"])
    for log in logs:
        writer.writerow([
            log.id, log.timestamp, log.user_id, log.action_type,
            log.resource_type, log.resource_id, log.module,
            log.action_details, log.success, log.ip_address,
        ])

    output.seek(0)
    filename = f"aeroguard_audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/modules")
def get_audit_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all distinct modules with event counts for filtering."""
    if not has_permission(current_user, VIEW_AUDIT_LOGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    logs = db.query(AuditLog.module).all()
    module_counts: dict = {}
    for (module,) in logs:
        if module:
            module_counts[module] = module_counts.get(module, 0) + 1
    return {"modules": module_counts}
