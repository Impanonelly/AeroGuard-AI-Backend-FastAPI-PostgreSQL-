from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class PilotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    employee_id: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default="pilot", pattern="^(pilot|co-pilot|crew)$")
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    duty_hours: Optional[float] = Field(None, ge=0)
    stress_level: Optional[float] = Field(None, ge=0, le=10)
    reaction_score: Optional[float] = Field(None, ge=0, le=100)
    alertness_score: Optional[float] = Field(None, ge=0, le=100)

class PilotCreate(PilotBase):
    pass

class PilotResponse(PilotBase):
    id: int
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True

class PilotAssessment(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    employee_id: str = Field(..., min_length=1, max_length=50)
    sleep_hours: float = Field(..., ge=0, le=24, description="Hours of sleep (0-24)")
    duty_hours: float = Field(..., ge=0, description="Duty hours")
    stress_level: float = Field(..., ge=0, le=10, description="Stress level (0-10)")
    reaction_score: Optional[float] = Field(None, ge=0, le=100, description="Reaction score (0-100)")
    alertness_score: Optional[float] = Field(None, ge=0, le=100, description="Alertness score (0-100)")

class AssessmentResponse(BaseModel):
    id: int
    name: str
    email: str
    employee_id: str
    risk_level: str
    sleep_hours: float
    duty_hours: float
    stress_level: float
    created_at: datetime

    class Config:
        from_attributes = True

