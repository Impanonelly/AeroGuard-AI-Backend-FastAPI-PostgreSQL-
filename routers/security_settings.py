from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from database import get_db
from models import User, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_SECURITY_SETTINGS, MANAGE_SECURITY_SETTINGS
from auth.utils import hash_password, verify_password

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class SessionTimeoutUpdate(BaseModel):
    timeout_seconds: int = Field(..., ge=300, le=86400)  # 5 min to 24 hours

class MFAToggleRequest(BaseModel):
    enable: bool
    mfa_secret: Optional[str] = None  # Required when enabling

class SecuritySettingsResponse(BaseModel):
    user_id: int
    mfa_enabled: bool
    session_timeout: int
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/")
def get_security_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current security settings for the authenticated user."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "mfa_enabled": current_user.mfa_enabled,
        "session_timeout_seconds": current_user.session_timeout,
        "session_timeout_minutes": round(current_user.session_timeout / 60, 1),
        "last_login": current_user.last_login,
        "is_active": current_user.is_active,
        "security_recommendations": _get_recommendations(current_user),
    }


@router.put("/session-timeout")
def update_session_timeout(
    data: SessionTimeoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update session inactivity timeout for the current user."""
    old_timeout = current_user.session_timeout
    current_user.session_timeout = data.timeout_seconds
    current_user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="session_timeout_updated",
        resource_type="user",
        resource_id=str(current_user.id),
        action_details=f"Session timeout changed: {old_timeout}s → {data.timeout_seconds}s",
        module="Security Settings",
        success=True,
    ))
    db.commit()
    return {
        "message": "Session timeout updated.",
        "timeout_seconds": data.timeout_seconds,
        "timeout_minutes": round(data.timeout_seconds / 60, 1),
    }


@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if not verify_password(data.current_password, current_user.password_hash):
        db.add(AuditLog(
            user_id=current_user.id,
            action_type="password_change_failed",
            resource_type="user",
            resource_id=str(current_user.id),
            action_details="Failed password change — incorrect current password",
            module="Security Settings",
            success=False,
            error_message="Incorrect current password",
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password.",
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters.",
        )

    current_user.password_hash = hash_password(data.new_password)
    current_user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="password_changed",
        resource_type="user",
        resource_id=str(current_user.id),
        action_details="Password changed successfully",
        module="Security Settings",
        success=True,
    ))
    db.commit()
    return {"message": "Password changed successfully. Please log in again with your new password."}


@router.post("/mfa/toggle")
def toggle_mfa(
    data: MFAToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable Multi-Factor Authentication."""
    if data.enable and not data.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MFA secret required to enable MFA.",
        )

    current_user.mfa_enabled = data.enable
    current_user.mfa_secret = data.mfa_secret if data.enable else None
    current_user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="mfa_enabled" if data.enable else "mfa_disabled",
        resource_type="user",
        resource_id=str(current_user.id),
        action_details=f"MFA {'enabled' if data.enable else 'disabled'} by user",
        module="Security Settings",
        success=True,
    ))
    db.commit()
    return {
        "message": f"MFA has been {'enabled' if data.enable else 'disabled'}.",
        "mfa_enabled": current_user.mfa_enabled,
    }


@router.get("/admin/overview")
def get_security_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    System-wide security overview. Administrator only.
    Shows MFA adoption, session config, and inactive accounts.
    """
    if not has_permission(current_user, MANAGE_SECURITY_SETTINGS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    all_users = db.query(User).all()
    active    = [u for u in all_users if u.is_active]
    mfa_on    = [u for u in active if u.mfa_enabled]

    from datetime import timedelta
    inactive_30d = [
        u for u in active
        if u.last_login and u.last_login < datetime.utcnow() - timedelta(days=30)
    ]

    return {
        "total_users": len(all_users),
        "active_users": len(active),
        "mfa_enabled_count": len(mfa_on),
        "mfa_adoption_rate": round(len(mfa_on) / len(active) * 100 if active else 0, 1),
        "inactive_30d": len(inactive_30d),
        "session_timeout_distribution": {
            "short_under_15m":   sum(1 for u in active if u.session_timeout < 900),
            "standard_15_30m":   sum(1 for u in active if 900 <= u.session_timeout < 1800),
            "extended_over_30m": sum(1 for u in active if u.session_timeout >= 1800),
        },
        "security_recommendations": [
            "Enforce MFA for all Administrator accounts." if any(u.role == "administrator" and not u.mfa_enabled for u in active) else None,
            f"Review {len(inactive_30d)} accounts inactive for 30+ days." if inactive_30d else None,
        ],
    }


def _get_recommendations(user: User) -> list:
    recs = []
    if not user.mfa_enabled:
        recs.append("Enable Multi-Factor Authentication (MFA) for enhanced account security.")
    if user.session_timeout > 1800:
        recs.append("Consider reducing session timeout to 30 minutes for better security posture.")
    if not user.last_login:
        recs.append("No login history found. Verify account configuration.")
    return recs
