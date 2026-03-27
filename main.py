from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from database import engine, get_db
from models import (
    Base, Pilot, User,
    HealthRecord, AlcoholScreening,
    DutyPeriod, FitnessAssessment,
    AuditLog, Notification
)
from schemas import PilotAssessment, AssessmentResponse, PilotResponse, PilotCreate
from routers import auth
from routers import alcohol, health, duty, assessment
from auth.dependencies import get_current_user
from auth.permissions import (
    require_supervisor_or_above,
    require_safety_officer_or_above,
    VIEW_CREW_DATA,
    VIEW_ALL_PERSONNEL,
    SUBMIT_ASSESSMENT,
    has_permission
)

app = FastAPI(
    title="AeroGuard AI Backend",
    description="Pilot Fatigue and Risk Assessment System",
    version="1.0.0"
)

# Configure CORS to allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vite default port
        "http://localhost:5173",  # Vite alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers including Authorization
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(alcohol.router, prefix="/alcohol", tags=["alcohol-substance"])
app.include_router(health.router, prefix="/health", tags=["health-records"])
app.include_router(duty.router, prefix="/duty", tags=["duty-management"])
app.include_router(assessment.router, prefix="/assessment", tags=["fitness-assessment"])

# Create ALL database tables (including new ones)
Base.metadata.create_all(bind=engine)

def calculate_risk(sleep: float, duty: float, stress: float) -> str:
    """
    Calculate risk level based on sleep hours, duty hours, and stress level.
    
    Risk scoring formula:
    - Sleep deficit: (8 - sleep) * 2
    - Duty hours: duty * 1.5
    - Stress: stress * 2
    
    Risk levels:
    - LOW: score < 10
    - MEDIUM: 10 <= score < 20
    - HIGH: score >= 20
    """
    score = (8 - sleep) * 2 + duty * 1.5 + stress * 2

    if score < 10:
        return "LOW"
    elif score < 20:
        return "MEDIUM"
    else:
        return "HIGH"

@app.get("/")
def read_root():
    return {
        "message": "AeroGuard AI Backend is running!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "assess": "/assess/",
            "pilots": "/pilots/",
            "pilot_by_id": "/pilots/{pilot_id}"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "AeroGuard AI Backend"}

@app.post("/assess/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def assess_pilot(
    assessment: PilotAssessment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assess a pilot's fatigue and risk level based on various metrics.
    
    SRS Requirement 1.3: All users with SUBMIT_ASSESSMENT permission can use this endpoint.
    Creates a new pilot assessment record and calculates risk level.
    """
    # Check permission (SRS Requirement 1.3)
    if not has_permission(current_user, SUBMIT_ASSESSMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not have permission to submit assessments."
        )
    # Check if pilot with email or employee_id already exists
    existing_pilot = db.query(Pilot).filter(
        (Pilot.email == assessment.email) | 
        (Pilot.employee_id == assessment.employee_id)
    ).first()
    
    if existing_pilot:
        # Update existing pilot record
        existing_pilot.name = assessment.name
        existing_pilot.sleep_hours = assessment.sleep_hours
        existing_pilot.duty_hours = assessment.duty_hours
        existing_pilot.stress_level = assessment.stress_level
        existing_pilot.reaction_score = assessment.reaction_score
        existing_pilot.alertness_score = assessment.alertness_score
        existing_pilot.risk_level = calculate_risk(
            assessment.sleep_hours,
            assessment.duty_hours,
            assessment.stress_level
        )
        
        db.commit()
        db.refresh(existing_pilot)
        return existing_pilot
    
    # Create new pilot record
    risk_level = calculate_risk(
        assessment.sleep_hours,
        assessment.duty_hours,
        assessment.stress_level
    )
    
    pilot = Pilot(
        name=assessment.name,
        email=assessment.email,
        employee_id=assessment.employee_id,
        role="pilot",
        sleep_hours=assessment.sleep_hours,
        duty_hours=assessment.duty_hours,
        stress_level=assessment.stress_level,
        reaction_score=assessment.reaction_score,
        alertness_score=assessment.alertness_score,
        risk_level=risk_level
    )

    db.add(pilot)
    db.commit()
    db.refresh(pilot)

    return pilot

@app.get("/pilots/", response_model=List[PilotResponse])
def get_all_pilots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all pilots with pagination support.
    
    SRS Requirement 1.3: Restricted to users with VIEW_CREW_DATA or VIEW_ALL_PERSONNEL permission.
    """
    # Check permissions (SRS Requirement 1.3)
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL)
    can_view_crew = has_permission(current_user, VIEW_CREW_DATA)
    
    if not (can_view_all or can_view_crew):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not have permission to view pilot data."
        )
    
    pilots = db.query(Pilot).offset(skip).limit(limit).all()
    return pilots

@app.get("/pilots/{pilot_id}", response_model=PilotResponse)
def get_pilot_by_id(
    pilot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific pilot by ID.
    
    SRS Requirement 1.3: Restricted to users with VIEW_CREW_DATA or VIEW_ALL_PERSONNEL permission.
    """
    # Check permissions
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL)
    can_view_crew = has_permission(current_user, VIEW_CREW_DATA)
    
    if not (can_view_all or can_view_crew):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not have permission to view pilot data."
        )
    pilot = db.query(Pilot).filter(Pilot.id == pilot_id).first()
    if not pilot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pilot with ID {pilot_id} not found"
        )
    return pilot

@app.get("/pilots/employee/{employee_id}", response_model=PilotResponse)
def get_pilot_by_employee_id(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific pilot by employee ID.
    
    SRS Requirement 1.3: Restricted to users with VIEW_CREW_DATA or VIEW_ALL_PERSONNEL permission.
    """
    # Check permissions
    can_view_all = has_permission(current_user, VIEW_ALL_PERSONNEL)
    can_view_crew = has_permission(current_user, VIEW_CREW_DATA)
    
    if not (can_view_all or can_view_crew):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not have permission to view pilot data."
        )
    pilot = db.query(Pilot).filter(Pilot.employee_id == employee_id).first()
    if not pilot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pilot with employee ID {employee_id} not found"
        )
    return pilot

@app.get("/pilots/risk/{risk_level}", response_model=List[PilotResponse])
def get_pilots_by_risk(
    risk_level: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_above)
):
    """
    Get all pilots with a specific risk level (LOW, MEDIUM, HIGH).
    
    SRS Requirement 1.3: Restricted to Supervisor role or above (supervisor, safety_officer, administrator).
    """
    if risk_level.upper() not in ["LOW", "MEDIUM", "HIGH"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk level must be LOW, MEDIUM, or HIGH"
        )
    
    pilots = db.query(Pilot).filter(Pilot.risk_level == risk_level.upper()).all()
    return pilots