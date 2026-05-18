from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from database import get_db
from models import User, UserRole, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, MANAGE_USERS, VIEW_ALL_PERSONNEL
from auth.utils import hash_password

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class UserCreateAdmin(BaseModel):
    email: str
    full_name: str
    employee_id: str
    role: str = UserRole.AVIATOR
    password: str = Field(..., min_length=8)
    license_number: Optional[str] = None
    certification_details: Optional[str] = None

class UserUpdateAdmin(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    license_number: Optional[str] = None
    certification_details: Optional[str] = None
    session_timeout: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    employee_id: str
    role: str
    is_active: bool
    mfa_enabled: bool
    license_number: Optional[str]
    certification_details: Optional[str]
    last_login: Optional[datetime]
    session_timeout: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users. Administrator only."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)

    return q.order_by(User.full_name).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a user by ID."""
    if not has_permission(current_user, VIEW_ALL_PERSONNEL) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user. Administrator only."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    if db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists.")

    valid_roles = [UserRole.AVIATOR, UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER,
                   UserRole.MEDICAL_OFFICER, UserRole.ADMINISTRATOR]
    if data.role not in valid_roles:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

    user = User(
        email=data.email,
        full_name=data.full_name,
        employee_id=data.employee_id,
        role=data.role,
        password_hash=hash_password(data.password),
        license_number=data.license_number,
        certification_details=data.certification_details,
        is_active=True,
    )
    db.add(user)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="user_created",
        resource_type="user",
        resource_id=data.employee_id,
        action_details=f"User created: {data.full_name} | Role: {data.role} | by Admin: {current_user.full_name}",
        module="User Management",
        success=True,
    ))
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user details. Administrator only."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    changes = []
    for field, value in data.dict(exclude_unset=True).items():
        old = getattr(user, field)
        setattr(user, field, value)
        changes.append(f"{field}: {old} → {value}")

    user.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="user_updated",
        resource_type="user",
        resource_id=str(user_id),
        action_details=f"User #{user_id} updated: {'; '.join(changes)}",
        module="User Management",
        success=True,
    ))
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a user account (soft delete). Administrator only."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="user_deactivated",
        resource_type="user",
        resource_id=str(user_id),
        action_details=f"User #{user_id} ({user.full_name}) deactivated by {current_user.full_name}",
        module="User Management",
        success=True,
    ))
    db.commit()
    return {"message": f"User {user.full_name} deactivated successfully.", "user_id": user_id}


@router.post("/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reactivate a previously deactivated user. Administrator only."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="user_reactivated",
        resource_type="user",
        resource_id=str(user_id),
        action_details=f"User #{user_id} ({user.full_name}) reactivated by {current_user.full_name}",
        module="User Management",
        success=True,
    ))
    db.commit()
    return {"message": f"User {user.full_name} reactivated successfully.", "user_id": user_id}


@router.get("/roles/summary")
def get_role_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Role-based user count summary."""
    if not has_permission(current_user, MANAGE_USERS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required.")

    roles = [UserRole.AVIATOR, UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER,
             UserRole.MEDICAL_OFFICER, UserRole.ADMINISTRATOR]
    summary = {}
    for role in roles:
        total   = db.query(User).filter(User.role == role).count()
        active  = db.query(User).filter(User.role == role, User.is_active == True).count()
        summary[role] = {"total": total, "active": active, "inactive": total - active}

    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),
        "by_role": summary,
    }
