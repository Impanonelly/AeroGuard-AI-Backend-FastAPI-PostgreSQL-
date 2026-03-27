# AeroGuard AI - Immediate Next Steps Checklist

## 🎯 Current Status
✅ Phase 1 Complete: Basic FastAPI backend, database connection, simple risk calculation

## 📋 Next Phase: Authentication & User Management (Phase 2)

### Step 1: User Model & Database Schema
**Estimated Time**: 2-3 hours

- [ ] Create `User` model in `models.py` with fields:
  - [ ] id, email, password_hash, full_name, employee_id
  - [ ] role (aviator, supervisor, safety_officer, administrator)
  - [ ] license_number, certification_details
  - [ ] is_active, created_at, updated_at
  - [ ] mfa_enabled, mfa_secret (optional for now)
  - [ ] last_login, session_timeout

- [ ] Create UserRole enum or constants
- [ ] Update `main.py` to create User table
- [ ] Test: Run server and verify User table created in PostgreSQL

**Test Command**:
```bash
# Check if table exists in pgAdmin or run:
psql -U postgres -d aeroguard_db -c "\d users"
```

---

### Step 2: Password Security
**Estimated Time**: 1-2 hours

- [ ] Update `requirements.txt`:
  ```txt
  passlib[bcrypt]==1.7.4
  python-jose[cryptography]==3.3.0
  ```

- [ ] Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Create `auth/` directory:
  ```bash
  mkdir auth
  touch auth/__init__.py
  ```

- [ ] Create `auth/utils.py`:
  - [ ] Import passlib and CryptContext
  - [ ] Create `hash_password()` function (12 rounds)
  - [ ] Create `verify_password()` function
  - [ ] Add password strength validation

- [ ] Test password hashing:
  ```python
  from auth.utils import hash_password, verify_password
  hashed = hash_password("test123")
  assert verify_password("test123", hashed) == True
  ```

---

### Step 3: JWT Authentication Setup
**Estimated Time**: 2-3 hours

- [ ] Create `auth/jwt_handler.py`:
  - [ ] Import jose.jwt and datetime
  - [ ] Set SECRET_KEY (move to .env later)
  - [ ] Create `create_access_token()` function (15 min expiry)
  - [ ] Create `create_refresh_token()` function (7 days expiry)
  - [ ] Create `verify_token()` function
  - [ ] Create `decode_token()` function

- [ ] Create `auth/dependencies.py`:
  - [ ] Create `get_current_user()` dependency
  - [ ] Create `get_current_active_user()` dependency
  - [ ] Add token validation logic

- [ ] Add to `.env`:
  ```env
  JWT_SECRET_KEY=your-super-secret-key-change-this
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=15
  REFRESH_TOKEN_EXPIRE_DAYS=7
  ```

- [ ] Test token generation:
  ```python
  from auth.jwt_handler import create_access_token
  token = create_access_token({"sub": "user@example.com"})
  print(token)  # Should print JWT token
  ```

---

### Step 4: User Registration Endpoint
**Estimated Time**: 2-3 hours

- [ ] Create `schemas/auth.py`:
  - [ ] `UserRegister` schema (email, password, full_name, employee_id, role)
  - [ ] `UserResponse` schema
  - [ ] `TokenResponse` schema

- [ ] Create `routers/` directory:
  ```bash
  mkdir routers
  touch routers/__init__.py
  ```

- [ ] Create `routers/auth.py`:
  - [ ] Import FastAPI, Depends, Session
  - [ ] Import schemas and models
  - [ ] Create `POST /auth/register` endpoint
  - [ ] Validate email uniqueness
  - [ ] Validate employee_id uniqueness
  - [ ] Hash password before storing
  - [ ] Create user in database
  - [ ] Return user response

- [ ] Update `main.py`:
  ```python
  from routers import auth
  app.include_router(auth.router, prefix="/auth", tags=["authentication"])
  ```

- [ ] Test registration:
  ```bash
  curl -X POST "http://localhost:8000/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "SecurePass123!",
      "full_name": "Test User",
      "employee_id": "EMP001",
      "role": "aviator"
    }'
  ```

---

### Step 5: User Login Endpoint
**Estimated Time**: 2-3 hours

- [ ] Create `UserLogin` schema in `schemas/auth.py`:
  - [ ] email, password fields

- [ ] Add to `routers/auth.py`:
  - [ ] `POST /auth/login` endpoint
  - [ ] Verify email exists
  - [ ] Verify password matches
  - [ ] Generate JWT access token
  - [ ] Generate JWT refresh token
  - [ ] Return tokens

- [ ] Test login:
  ```bash
  curl -X POST "http://localhost:8000/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "SecurePass123!"
    }'
  ```

- [ ] Verify response contains access_token and refresh_token

---

### Step 6: Token Refresh Endpoint
**Estimated Time**: 1-2 hours

- [ ] Add to `routers/auth.py`:
  - [ ] `POST /auth/refresh` endpoint
  - [ ] Validate refresh token
  - [ ] Generate new access token
  - [ ] Return new access token

- [ ] Test token refresh

---

### Step 7: Protected Endpoints
**Estimated Time**: 1-2 hours

- [ ] Update existing endpoints to require authentication:
  - [ ] Add `current_user: User = Depends(get_current_user)` to endpoints
  - [ ] Test: Try accessing without token (should get 401)
  - [ ] Test: Try accessing with valid token (should work)

- [ ] Update `POST /assess/` to require authentication
- [ ] Update `GET /pilots/` to require authentication

---

### Step 8: Role-Based Access Control (RBAC)
**Estimated Time**: 2-3 hours

- [ ] Create `auth/permissions.py`:
  - [ ] Define permission constants
  - [ ] Create `require_role()` decorator
  - [ ] Create `require_permission()` decorator

- [ ] Apply permissions:
  - [ ] Admin-only endpoints
  - [ ] Supervisor-only endpoints
  - [ ] Test permission enforcement

---

## 🧪 Testing Checklist

After completing each step, test:

- [ ] Server starts without errors
- [ ] Database tables created correctly
- [ ] Endpoints return expected responses
- [ ] Error handling works (invalid input, missing data)
- [ ] Authentication works (login, token validation)
- [ ] Permissions work (role-based access)

---

## 📝 Code Quality Checklist

- [ ] All functions have docstrings
- [ ] Type hints used everywhere
- [ ] Error handling implemented
- [ ] Input validation with Pydantic
- [ ] No hardcoded secrets (use .env)
- [ ] Code follows PEP 8 style guide

---

## 🚀 Quick Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate

# Install new dependencies
pip install package-name
pip freeze > requirements.txt

# Run server
uvicorn main:app --reload

# Check database
psql -U postgres -d aeroguard_db

# Test endpoint
curl http://localhost:8000/health

# View API docs
# Open browser: http://localhost:8000/docs
```

---

## 📚 Resources

- FastAPI Authentication: https://fastapi.tiangolo.com/tutorial/security/
- JWT with Python: https://python-jose.readthedocs.io/
- Password Hashing: https://passlib.readthedocs.io/

---

## ⏱️ Estimated Timeline

- **Step 1-2**: Day 1 (4-5 hours)
- **Step 3-4**: Day 2 (4-5 hours)
- **Step 5-6**: Day 3 (3-4 hours)
- **Step 7-8**: Day 4 (3-4 hours)

**Total**: ~15-18 hours (2-3 days of focused work)

---

## 🎯 Success Criteria

Phase 2 is complete when:
- ✅ Users can register with email/password
- ✅ Users can login and receive JWT tokens
- ✅ Protected endpoints require authentication
- ✅ Role-based permissions are enforced
- ✅ All endpoints tested and working

---

## 🔄 After Phase 2

Once authentication is complete, move to:
- **Phase 3**: Complete Database Schema (Health records, Duty management, etc.)
- **Phase 4**: Alcohol & Substance Monitoring (Critical for compliance)

---

**Remember**: Build incrementally, test frequently, commit often! 🚀

