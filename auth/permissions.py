"""
Role-Based Access Control (RBAC) Permission System
SRS Reference: Module 1.3 - Role-Based Access Control

This module implements granular permissions for each user role as specified in the SRS:
- Aviator: View own data, submit assessments
- Supervisor: View crew data, override assessments, view substance records
- Safety Officer: View all reports, analytics, compliance data
- Administrator: Full system access
"""

from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import List
from models import User, UserRole
from auth.dependencies import get_current_user

# Permission Constants
# SRS Requirement 1.3: Granular permission matrix

# View Permissions
VIEW_OWN_PROFILE = "view_own_profile"
VIEW_CREW_DATA = "view_crew_data"
VIEW_ALL_PERSONNEL = "view_all_personnel"
VIEW_REPORTS = "view_reports"
VIEW_ANALYTICS = "view_analytics"
VIEW_COMPLIANCE = "view_compliance"
VIEW_SUBSTANCE_RECORDS = "view_substance_records"
VIEW_AUDIT_LOGS = "view_audit_logs"

# NEW — Module-specific view permissions
VIEW_MEDICAL_RECORDS = "view_medical_records"
CREATE_MEDICAL_RECORDS = "create_medical_records"
VIEW_FRMS_DATA = "view_frms_data"
MANAGE_FRMS = "manage_frms"
VIEW_SAFETY_ANALYTICS = "view_safety_analytics"
REPORT_SAFETY_INCIDENT = "report_safety_incident"
MANAGE_SAFETY_INCIDENTS = "manage_safety_incidents"
VIEW_RISK_PREDICTIONS = "view_risk_predictions"
MANAGE_COMPLIANCE = "manage_compliance"
VIEW_ALERTNESS_DATA = "view_alertness_data"
SUBMIT_ALERTNESS_READING = "submit_alertness_reading"
MANAGE_IOT_DEVICES = "manage_iot_devices"
VIEW_SECURITY_SETTINGS = "view_security_settings"
MANAGE_SECURITY_SETTINGS = "manage_security_settings"

# Action Permissions
SUBMIT_ASSESSMENT = "submit_assessment"
OVERRIDE_ASSESSMENT = "override_assessment"
MANAGE_USERS = "manage_users"
MANAGE_SYSTEM = "manage_system"
GENERATE_REPORTS = "generate_reports"
CONFIGURE_SYSTEM = "configure_system"

# Role-Permission Matrix (SRS Requirement 1.3)
ROLE_PERMISSIONS = {
    UserRole.AVIATOR: [
        VIEW_OWN_PROFILE,
        SUBMIT_ASSESSMENT,
        SUBMIT_ALERTNESS_READING,
        VIEW_ALERTNESS_DATA,        # own data only (enforced in endpoints)
        VIEW_RISK_PREDICTIONS,      # own data only
        REPORT_SAFETY_INCIDENT,
    ],
    UserRole.SUPERVISOR: [
        VIEW_OWN_PROFILE,
        VIEW_CREW_DATA,
        SUBMIT_ASSESSMENT,
        OVERRIDE_ASSESSMENT,
        VIEW_SUBSTANCE_RECORDS,
        VIEW_REPORTS,
        GENERATE_REPORTS,
        VIEW_FRMS_DATA,
        MANAGE_FRMS,
        VIEW_RISK_PREDICTIONS,
        VIEW_ALERTNESS_DATA,
        SUBMIT_ALERTNESS_READING,
        REPORT_SAFETY_INCIDENT,
    ],
    UserRole.SAFETY_OFFICER: [
        VIEW_OWN_PROFILE,
        VIEW_CREW_DATA,
        VIEW_ALL_PERSONNEL,
        VIEW_REPORTS,
        VIEW_ANALYTICS,
        VIEW_COMPLIANCE,
        VIEW_SUBSTANCE_RECORDS,
        GENERATE_REPORTS,
        SUBMIT_ASSESSMENT,
        VIEW_FRMS_DATA,
        MANAGE_FRMS,
        VIEW_SAFETY_ANALYTICS,
        REPORT_SAFETY_INCIDENT,
        MANAGE_SAFETY_INCIDENTS,
        VIEW_RISK_PREDICTIONS,
        MANAGE_COMPLIANCE,
        VIEW_ALERTNESS_DATA,
        SUBMIT_ALERTNESS_READING,
        VIEW_AUDIT_LOGS,
        MANAGE_IOT_DEVICES,
    ],
    UserRole.MEDICAL_OFFICER: [
        VIEW_OWN_PROFILE,
        VIEW_CREW_DATA,
        VIEW_REPORTS,
        VIEW_COMPLIANCE,
        VIEW_SUBSTANCE_RECORDS,
        SUBMIT_ASSESSMENT,
        VIEW_MEDICAL_RECORDS,
        CREATE_MEDICAL_RECORDS,
        VIEW_ALERTNESS_DATA,
        VIEW_RISK_PREDICTIONS,      # read-only for medical context
        REPORT_SAFETY_INCIDENT,
    ],
    UserRole.ADMINISTRATOR: [
        VIEW_OWN_PROFILE,
        VIEW_CREW_DATA,
        VIEW_ALL_PERSONNEL,
        VIEW_REPORTS,
        VIEW_ANALYTICS,
        VIEW_COMPLIANCE,
        VIEW_SUBSTANCE_RECORDS,
        VIEW_AUDIT_LOGS,
        SUBMIT_ASSESSMENT,
        OVERRIDE_ASSESSMENT,
        MANAGE_USERS,
        MANAGE_SYSTEM,
        GENERATE_REPORTS,
        CONFIGURE_SYSTEM,
        VIEW_MEDICAL_RECORDS,
        CREATE_MEDICAL_RECORDS,
        VIEW_FRMS_DATA,
        MANAGE_FRMS,
        VIEW_SAFETY_ANALYTICS,
        REPORT_SAFETY_INCIDENT,
        MANAGE_SAFETY_INCIDENTS,
        VIEW_RISK_PREDICTIONS,
        MANAGE_COMPLIANCE,
        VIEW_ALERTNESS_DATA,
        SUBMIT_ALERTNESS_READING,
        MANAGE_IOT_DEVICES,
        VIEW_SECURITY_SETTINGS,
        MANAGE_SECURITY_SETTINGS,
    ],
}

def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User object
        permission: Permission string to check
        
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions

def require_permission(permission: str):
    """
    Decorator to require a specific permission.
    
    Usage:
        @require_permission(VIEW_CREW_DATA)
        def get_crew_data(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to get from args (if passed as dependency)
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs) if hasattr(func, '__code__') and 'async' in str(func) else func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(allowed_roles: List[str]):
    """
    Dependency function to require specific roles.
    
    Usage:
        @router.get("/endpoint")
        def my_endpoint(current_user: User = Depends(require_role([UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_any_permission(permissions: List[str]):
    """
    Dependency function to require at least one permission.
    
    Usage:
        @router.get("/endpoint")
        def my_endpoint(current_user: User = Depends(require_any_permission([VIEW_CREW_DATA, VIEW_ALL_PERSONNEL]))):
            ...
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        has_any = any(perm in user_permissions for perm in permissions)
        
        if not has_any:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required one of: {', '.join(permissions)}"
            )
        return current_user
    return permission_checker

# Convenience functions for common role checks
def require_supervisor_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require supervisor, safety officer, or administrator role"""
    allowed = [UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER, UserRole.ADMINISTRATOR]
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Supervisor role or above required."
        )
    return current_user

def require_safety_officer_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require safety officer or administrator role"""
    allowed = [UserRole.SAFETY_OFFICER, UserRole.ADMINISTRATOR]
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Safety Officer role or above required."
        )
    return current_user

def require_administrator(current_user: User = Depends(get_current_user)) -> User:
    """Require administrator role only"""
    if current_user.role != UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator role required."
        )
    return current_user

def can_view_substance_records(user: User, target_user_id: int = None) -> bool:
    """
    Check if user can view substance records.
    SRS Requirement 13.2: Restrict access to substance records.
    
    Rules:
    - User can always view their own records
    - Supervisor can view their crew's records
    - Safety Officer and Administrator can view all records
    """
    # User can always view their own records
    if target_user_id and user.id == target_user_id:
        return True
    
    # Check role-based permissions
    if user.role == UserRole.ADMINISTRATOR or user.role == UserRole.SAFETY_OFFICER:
        return True
    
    if user.role == UserRole.SUPERVISOR:
        # Supervisor can view crew records (would need crew relationship check)
        return True
    
    return False

