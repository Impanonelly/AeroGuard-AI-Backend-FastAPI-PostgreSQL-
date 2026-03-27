from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from models import UserRole

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=100)
    employee_id: str = Field(..., min_length=1, max_length=50)
    role: str = Field(
        default=UserRole.AVIATOR,
        description="User role: aviator, supervisor, safety_officer, administrator"
    )
    license_number: Optional[str] = Field(None, max_length=50)
    certification_details: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: int
    email: str
    full_name: str
    employee_id: str
    role: str
    license_number: Optional[str] = None
    certification_details: Optional[str] = None
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str

