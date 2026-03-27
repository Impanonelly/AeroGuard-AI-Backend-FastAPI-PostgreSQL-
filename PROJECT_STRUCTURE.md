# AeroGuard AI - Project Structure Guide

This document explains the recommended project structure and organization for the AeroGuard AI backend.

## Directory Structure

```
aeroguard_backend/
│
├── main.py                    # FastAPI application entry point
├── database.py               # Database connection and session management
├── models.py                 # SQLAlchemy ORM models (all database tables)
├── schemas.py                # Pydantic schemas (request/response validation)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation
├── DEVELOPMENT_ROADMAP.md    # Complete development roadmap
├── QUICK_START_GUIDE.md      # Quick start guide
├── PROJECT_STRUCTURE.md      # This file
│
├── auth/                     # Authentication & Authorization Module
│   ├── __init__.py
│   ├── jwt_handler.py        # JWT token creation and validation
│   ├── dependencies.py       # FastAPI dependencies for auth
│   ├── permissions.py        # RBAC permission decorators
│   ├── utils.py              # Password hashing, validation utilities
│   └── mfa.py                # Multi-factor authentication
│
├── routers/                  # API Route Handlers (Controllers)
│   ├── __init__.py
│   ├── auth.py               # Authentication routes (login, register, etc.)
│   ├── pilots.py             # Pilot management routes
│   ├── assessments.py        # Fitness-for-duty assessment routes
│   ├── alcohol.py            # Alcohol screening routes
│   ├── substance.py          # Substance screening routes
│   ├── duty.py               # Duty period management routes
│   ├── health.py             # Health record management routes
│   ├── reports.py            # Report generation routes
│   ├── notifications.py      # Notification and alert routes
│   ├── compliance.py         # Compliance tracking routes
│   └── admin.py              # Administrator routes
│
├── services/                 # Business Logic Layer
│   ├── __init__.py
│   ├── alertness_calculator.py    # Alertness score calculation
│   ├── risk_predictor.py          # Risk level prediction
│   ├── fatigue_model.py           # Fatigue accumulation modeling
│   ├── circadian_calculator.py    # Circadian rhythm calculations
│   ├── readiness_assessor.py      # Fitness-for-duty assessment
│   ├── screening_workflow.py      # Alcohol/substance screening workflow
│   ├── crew_pairing.py            # Crew compatibility analysis
│   ├── icao_compliance.py         # ICAO compliance checking
│   ├── scheduling_optimizer.py     # Fatigue-based scheduling
│   ├── notification_service.py    # Notification delivery service
│   ├── alert_service.py           # Alert generation and escalation
│   ├── report_generator.py        # PDF/Excel report generation
│   ├── encryption.py              # Data encryption utilities
│   └── audit_logger.py            # Audit log management
│
├── ai/                       # AI/ML Models and Services
│   ├── __init__.py
│   ├── config.py             # AI model configuration
│   ├── models/               # Trained model files (.pkl, .h5, etc.)
│   │   ├── fatigue_model.pkl
│   │   ├── risk_classifier.pkl
│   │   └── pattern_recognition.pkl
│   ├── training/             # Model training scripts
│   │   ├── __init__.py
│   │   ├── fatigue_model.py
│   │   ├── risk_classifier.py
│   │   └── pattern_recognition.py
│   └── prediction/           # Prediction services
│       ├── __init__.py
│       ├── fatigue_predictor.py
│       ├── risk_classifier.py
│       └── pattern_analyzer.py
│
├── schemas/                  # Pydantic Schemas (organized by module)
│   ├── __init__.py
│   ├── auth.py              # Authentication schemas
│   ├── user.py              # User schemas
│   ├── pilot.py             # Pilot schemas
│   ├── assessment.py        # Assessment schemas
│   ├── alcohol.py           # Alcohol screening schemas
│   ├── substance.py         # Substance screening schemas
│   ├── duty.py              # Duty management schemas
│   ├── health.py            # Health record schemas
│   ├── readiness.py         # Readiness assessment schemas
│   ├── notification.py      # Notification schemas
│   └── report.py            # Report schemas
│
├── models/                   # SQLAlchemy Models (organized by module)
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── pilot.py             # Pilot model
│   ├── health.py            # Health record models
│   ├── alcohol.py           # Alcohol screening model
│   ├── substance.py         # Substance screening model
│   ├── duty.py              # Duty period models
│   ├── assessment.py        # Assessment models
│   ├── notification.py      # Notification models
│   ├── compliance.py        # Compliance models
│   └── audit.py             # Audit log model
│
├── tests/                    # Test Files
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── test_auth.py         # Authentication tests
│   ├── test_assessments.py  # Assessment tests
│   ├── test_screening.py    # Screening tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_services.py     # Service layer tests
│   └── test_ai.py           # AI model tests
│
├── migrations/               # Database Migrations (Alembic)
│   ├── versions/            # Migration version files
│   ├── env.py              # Alembic environment
│   └── alembic.ini         # Alembic configuration
│
├── templates/                # Report Templates
│   ├── reports/
│   │   ├── safety_report.html
│   │   ├── compliance_report.html
│   │   └── substance_report.html
│   └── emails/
│       ├── alert_notification.html
│       └── reminder_email.html
│
├── static/                   # Static Files
│   ├── certificates/        # Generated readiness certificates
│   ├── reports/             # Generated reports (PDF/Excel)
│   └── lab_results/         # Imported lab result PDFs
│
└── config/                   # Configuration Files
    ├── __init__.py
    ├── settings.py          # Application settings
    ├── database.py          # Database configuration
    └── security.py          # Security configuration
```

## File Organization Principles

### 1. Separation of Concerns
- **routers/**: Handle HTTP requests/responses only
- **services/**: Contain all business logic
- **models/**: Database table definitions
- **schemas/**: Data validation and serialization

### 2. Module-Based Organization
Group related functionality together:
- All authentication code in `auth/`
- All AI/ML code in `ai/`
- All route handlers in `routers/`

### 3. Single Responsibility
Each file should have one clear purpose:
- `jwt_handler.py` only handles JWT tokens
- `alertness_calculator.py` only calculates alertness scores
- `alcohol.py` router only handles alcohol screening routes

## Module Descriptions

### auth/
Handles all authentication and authorization:
- JWT token management
- Password hashing and verification
- Role-based access control
- Multi-factor authentication

### routers/
FastAPI route handlers. Each router file corresponds to a feature area:
- `auth.py`: Login, register, logout, MFA
- `alcohol.py`: Alcohol screening endpoints
- `substance.py`: Substance screening endpoints
- `assessments.py`: Fitness-for-duty assessments

### services/
Business logic layer. Services are called by routers:
- `alertness_calculator.py`: Calculates alertness scores
- `screening_workflow.py`: Manages screening workflows
- `notification_service.py`: Sends notifications

### ai/
AI/ML model management:
- `training/`: Scripts to train models
- `prediction/`: Services to use trained models
- `models/`: Stored trained model files

### schemas/
Pydantic models for request/response validation:
- Input validation
- Response serialization
- Data transformation

### models/
SQLAlchemy ORM models:
- Database table definitions
- Relationships between tables
- Database constraints

## Import Patterns

### In Routers
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import get_current_user
from services.alertness_calculator import calculate_alertness
from schemas.assessment import AssessmentCreate, AssessmentResponse
```

### In Services
```python
from sqlalchemy.orm import Session
from models.pilot import Pilot
from models.health import HealthRecord
from services.circadian_calculator import get_circadian_factor
```

### In Models
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
```

## Naming Conventions

### Files
- Use lowercase with underscores: `alertness_calculator.py`
- Router files match feature: `alcohol.py`, `substance.py`
- Service files describe function: `risk_predictor.py`

### Classes
- PascalCase: `Pilot`, `HealthRecord`, `AlcoholScreening`
- Models: `User`, `Pilot`, `DutyPeriod`
- Schemas: `UserCreate`, `AssessmentResponse`

### Functions
- snake_case: `calculate_alertness()`, `get_current_user()`
- Verbs for actions: `create_user()`, `assess_pilot()`

### Variables
- snake_case: `user_id`, `risk_level`, `bac_level`

## Dependency Flow

```
Request → Router → Service → Model → Database
                ↓
            Schema (validation)
                ↓
            Response
```

Example:
1. Client sends POST request to `/assess/`
2. `routers/assessments.py` receives request
3. Validates with `schemas/assessment.py`
4. Calls `services/readiness_assessor.py`
5. Service uses `models/pilot.py` to query database
6. Returns response using `schemas/assessment.py`

## Adding New Features

When adding a new feature (e.g., "Flight Tracking"):

1. **Create Model**: `models/flight.py`
   ```python
   class Flight(Base):
       __tablename__ = "flights"
       # ... fields
   ```

2. **Create Schema**: `schemas/flight.py`
   ```python
   class FlightCreate(BaseModel):
       # ... fields
   ```

3. **Create Service**: `services/flight_tracker.py`
   ```python
   def track_flight(flight_data):
       # ... business logic
   ```

4. **Create Router**: `routers/flight.py`
   ```python
   @router.post("/flights/")
   def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
       # ... route handler
   ```

5. **Register Router**: In `main.py`
   ```python
   from routers import flight
   app.include_router(flight.router, prefix="/api/v1", tags=["flights"])
   ```

## Best Practices

1. **Keep Routers Thin**: Routers should only handle HTTP concerns
2. **Business Logic in Services**: All calculations and logic in services
3. **Reusable Services**: Services can call other services
4. **Schema Validation**: Always validate input with Pydantic
5. **Error Handling**: Use HTTPException for API errors
6. **Type Hints**: Use type hints everywhere
7. **Docstrings**: Document all functions and classes
8. **Testing**: Write tests for services and routers

## Migration Strategy

As you build, you'll need to migrate from the current flat structure:

**Current** (Phase 1):
```
main.py
models.py
schemas.py
database.py
```

**Target** (Phase 2+):
```
main.py
database.py
models/
schemas/
routers/
services/
auth/
```

**Migration Steps**:
1. Create new directory structure
2. Move code to appropriate modules
3. Update imports
4. Test everything still works
5. Remove old files

## Example: Complete Feature Implementation

### Feature: Alcohol Screening

**1. Model** (`models/alcohol.py`):
```python
class AlcoholScreening(Base):
    __tablename__ = "alcohol_screenings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bac_level = Column(Float)
    # ... more fields
```

**2. Schema** (`schemas/alcohol.py`):
```python
class AlcoholScreeningCreate(BaseModel):
    bac_level: float = Field(..., ge=0.0, le=1.0)
    # ... more fields
```

**3. Service** (`services/screening_workflow.py`):
```python
def record_alcohol_screening(data, db):
    if data.bac_level > 0.04:
        trigger_violation_alert(data.user_id)
    # ... logic
```

**4. Router** (`routers/alcohol.py`):
```python
@router.post("/alcohol/pre-flight")
def record_preflight_screening(
    screening: AlcoholScreeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return screening_service.record_screening(screening, db)
```

This structure ensures:
- Clear separation of concerns
- Easy to find code
- Scalable architecture
- Testable components
- Maintainable codebase

