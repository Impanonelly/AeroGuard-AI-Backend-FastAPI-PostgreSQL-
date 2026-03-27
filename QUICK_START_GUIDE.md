# AeroGuard AI - Quick Start Development Guide

## Current Status ✅
- **Phase 1**: COMPLETE - Basic FastAPI backend, database connection, simple risk calculation

## Immediate Next Steps (Next 2 Weeks)

### Week 1: Authentication Foundation

#### Day 1-2: User Model & Database
```bash
# Tasks:
1. Create User model in models.py
2. Add UserRole enum
3. Create database migration
4. Test User table creation
```

#### Day 3-4: Password Security
```bash
# Tasks:
1. Install passlib[bcrypt] and python-jose
2. Create auth/utils.py with password hashing
3. Test password hashing and verification
```

#### Day 5: JWT Setup
```bash
# Tasks:
1. Create auth/jwt_handler.py
2. Create auth/dependencies.py
3. Set up JWT secret in .env
4. Test token generation
```

### Week 2: Authentication Endpoints

#### Day 1-2: Registration
```bash
# Tasks:
1. Create schemas/auth.py
2. Create routers/auth.py
3. Implement POST /auth/register
4. Test registration endpoint
```

#### Day 3-4: Login & Tokens
```bash
# Tasks:
1. Implement POST /auth/login
2. Implement POST /auth/refresh
3. Implement POST /auth/logout
4. Test authentication flow
```

#### Day 5: RBAC
```bash
# Tasks:
1. Create auth/permissions.py
2. Define permission matrix
3. Apply permissions to endpoints
4. Test role-based access
```

---

## Project Structure (Recommended)

```
aeroguard_backend/
├── main.py                 # FastAPI app entry point
├── database.py             # Database connection
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic schemas
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── .gitignore
├── README.md
├── DEVELOPMENT_ROADMAP.md
│
├── auth/                   # Authentication module
│   ├── __init__.py
│   ├── jwt_handler.py      # JWT token management
│   ├── dependencies.py     # Auth dependencies
│   ├── permissions.py      # RBAC permissions
│   ├── utils.py            # Password hashing, etc.
│   └── mfa.py              # Multi-factor auth
│
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── auth.py             # Authentication routes
│   ├── pilots.py           # Pilot management
│   ├── assessments.py      # Fitness assessments
│   ├── alcohol.py          # Alcohol screening
│   ├── substance.py        # Substance screening
│   ├── duty.py             # Duty management
│   ├── reports.py          # Reporting
│   └── admin.py            # Admin functions
│
├── services/               # Business logic
│   ├── __init__.py
│   ├── alertness_calculator.py
│   ├── risk_predictor.py
│   ├── fatigue_model.py
│   ├── readiness_assessor.py
│   ├── screening_workflow.py
│   ├── notification_service.py
│   └── report_generator.py
│
├── ai/                     # AI/ML models
│   ├── __init__.py
│   ├── models/             # Trained model files
│   ├── training/            # Training scripts
│   └── prediction/         # Prediction services
│
├── tests/                  # Test files
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_assessments.py
│   └── test_api.py
│
└── migrations/              # Database migrations (Alembic)
    └── versions/
```

---

## Development Commands

### Setup
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py
```

### Database
```bash
# Create migration (when using Alembic)
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Key Files to Create Next

### 1. auth/__init__.py
```python
# Empty file to make auth a package
```

### 2. auth/utils.py
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### 3. auth/jwt_handler.py
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

SECRET_KEY = "your-secret-key"  # Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Implementation here
    pass

def verify_token(token: str):
    # Implementation here
    pass
```

---

## Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:impano12@127.0.0.1:5432/aeroguard_db

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
BCRYPT_ROUNDS=12
MFA_ENABLED=true

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Redis (for Celery and caching)
REDIS_URL=redis://localhost:6379/0

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=aeroguard-reports
```

---

## Testing Checklist

After each phase, test:

- [ ] All endpoints return correct status codes
- [ ] Authentication works (login, register, logout)
- [ ] RBAC permissions enforced correctly
- [ ] Database operations work (CRUD)
- [ ] Error handling works (404, 401, 403, 500)
- [ ] Input validation works (Pydantic schemas)
- [ ] JWT tokens expire correctly
- [ ] Password hashing works
- [ ] Database relationships work

---

## Common Issues & Solutions

### Issue: Import errors
**Solution**: Make sure all `__init__.py` files exist in package directories

### Issue: Database connection fails
**Solution**: Check PostgreSQL is running and DATABASE_URL is correct

### Issue: JWT token invalid
**Solution**: Check SECRET_KEY matches and token hasn't expired

### Issue: Permission denied
**Solution**: Check user role and permission decorators

---

## Progress Tracking

Use this checklist to track your progress:

### Phase 2: Authentication
- [ ] User model created
- [ ] Password hashing implemented
- [ ] JWT authentication working
- [ ] Registration endpoint working
- [ ] Login endpoint working
- [ ] RBAC implemented
- [ ] MFA implemented (optional for MVP)

### Phase 3: Database Schema
- [ ] Health records model
- [ ] Duty management models
- [ ] Assessment models
- [ ] Notification models
- [ ] Compliance models

### Phase 4: Alcohol & Substance
- [ ] Alcohol screening model
- [ ] Pre-flight screening endpoint
- [ ] Post-flight screening endpoint
- [ ] Substance screening endpoints
- [ ] Violation management
- [ ] Mandatory workflow

---

## Next Phase Preview

After completing Phase 2 (Authentication), you'll move to:

**Phase 3: Complete Database Schema**
- Create all data models
- Set up relationships
- Create migrations
- Test database operations

Then **Phase 4: Alcohol & Substance Monitoring** (Critical for compliance)

---

## Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- JWT Guide: https://jwt.io/introduction
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

## Questions to Consider

Before starting each phase, ask:

1. **What data do I need to store?** → Create models
2. **What operations do I need?** → Create endpoints
3. **Who can access this?** → Set permissions
4. **How do I validate input?** → Create schemas
5. **What business logic is needed?** → Create services
6. **How do I test this?** → Write tests

---

Good luck with your Final Year Project! 🚀

Remember: Build incrementally, test frequently, and document as you go.

