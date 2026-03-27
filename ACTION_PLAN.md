# AeroGuard AI - Action Plan Based on SRS Requirements

## 📊 Current Status vs SRS Requirements

### ✅ What's Complete (Phase 1 - Foundation)
According to your SRS Section 7 (Current Implementation Status):

| Component | SRS Requirement | Status | Notes |
|-----------|----------------|--------|-------|
| Python 3.14 | ✅ Required | ✅ Complete | Installed |
| PostgreSQL 16 | ✅ Required | ✅ Complete | Running on localhost:5432 |
| FastAPI + Uvicorn | ✅ Required | ✅ Complete | Running on port 8000 |
| SQLAlchemy ORM | ✅ Required | ✅ Complete | v2.0.48 |
| Database Connection | ✅ Required | ✅ Complete | Connected to aeroguard_db |
| Basic Pilot Model | ✅ Required | ✅ Complete | pilots table created |
| Basic Risk Calculation | ✅ Required | ✅ Complete | Low/Medium/High |

### 🔄 What's In Progress (Phase 2 - Authentication)
According to your SRS Module 1 (User Registration & Authentication):

| Requirement | SRS Section | Status | Priority |
|-------------|-------------|--------|----------|
| User Registration | 1.1 | ✅ 80% Complete | CRITICAL |
| JWT Authentication | 1.2 | ✅ 80% Complete | CRITICAL |
| Password Security (bcrypt) | 1.2 | ✅ Complete | CRITICAL |
| Role-Based Access Control | 1.3 | ⏳ Next Step | CRITICAL |
| MFA Support | 1.2 | ⏳ Pending | HIGH |

---

## 🎯 Immediate Action Plan (Following SRS Requirements)

### STEP 1: Complete Phase 2 - Authentication (This Week)
**SRS Reference**: Module 1 - User Registration & Authentication

#### Task 1.1: Finish RBAC (Role-Based Access Control)
**SRS Requirement 1.3**: "The system shall implement Role-Based Access Control (RBAC) with a granular permission matrix"

**What to do:**
1. Create `auth/permissions.py` with permission decorators
2. Define permission matrix for each role:
   - Aviator: View own data, submit assessments
   - Supervisor: View crew data, override assessments, view substance records
   - Safety Officer: View all reports, analytics, compliance data
   - Administrator: Full system access
3. Apply permissions to existing endpoints

**Files to create:**
- `auth/permissions.py`

**Time**: 2-3 hours

---

#### Task 1.2: Protect Existing Endpoints
**SRS Requirement 1.3**: "The system shall restrict access to sensitive modules"

**What to do:**
1. Add authentication to `/assess/` endpoint
2. Add authentication to `/pilots/` endpoints
3. Apply role-based permissions
4. Test with different user roles

**Files to modify:**
- `main.py` - Add auth dependencies to endpoints
- `routers/auth.py` - Add permission decorators

**Time**: 1-2 hours

---

### STEP 2: Phase 3 - Complete Database Schema (Next Week)
**SRS Reference**: Module 3 - Personnel Health Monitoring, Module 7 - Flight Duty Management

#### Task 2.1: Health Records Model
**SRS Requirement 3.1**: "The system shall support health data entry for: sleep hours, stress level, heart rate, blood pressure, alcohol BAC level, and substance screening results"

**What to create:**
- `models/health.py` - HealthRecord model
- `models/alcohol.py` - AlcoholScreening model
- `models/substance.py` - SubstanceScreening model

**Time**: 3-4 hours

---

#### Task 2.2: Duty Management Models
**SRS Requirement 7.1**: "The system shall track all duty periods and rest times for every aviation personnel member"

**What to create:**
- `models/duty.py` - DutyPeriod, RestPeriod, FlightTimeLimit models

**Time**: 2-3 hours

---

### STEP 3: Phase 4 - Alcohol & Substance Monitoring (CRITICAL - Week 3)
**SRS Reference**: Module 14 - Alcohol & Substance Monitoring (Safety-Critical)

This is the MOST CRITICAL module according to your SRS. It's required for ICAO compliance.

#### Task 3.1: Pre-Flight Alcohol Screening
**SRS Requirement 14.1**: "The system shall require every aviation personnel member to complete an alcohol breath test (BAC screening) before every duty period"

**What to create:**
- `routers/alcohol.py` - Alcohol screening endpoints
- `services/screening_workflow.py` - Screening workflow logic
- Enforce 0.04% BAC limit (ICAO Doc 9654)

**Time**: 4-5 hours

---

#### Task 3.2: Substance Screening
**SRS Requirement 14.3**: "The system shall support recording of substance screening results"

**What to create:**
- `routers/substance.py` - Substance screening endpoints
- Status workflow: Cleared/Flagged/Pending
- Block duty if Flagged or Pending

**Time**: 3-4 hours

---

## 📋 How We'll Work (Step-by-Step Process)

### Working Method:
1. **I'll create the code** following your SRS requirements exactly
2. **You test it** in VS Code
3. **We fix any issues** together
4. **Move to next task** when current one works

### For Each Task:
1. ✅ I create/modify files according to SRS
2. ✅ You install dependencies if needed
3. ✅ You test the endpoints
4. ✅ We verify it matches SRS requirements
5. ✅ Move to next task

---

## 🚀 Let's Start: Complete Phase 2 First

### Right Now - Let's Finish Authentication:

**I'll create:**
1. `auth/permissions.py` - RBAC permission system
2. Update endpoints to use permissions
3. Test the complete auth system

**You'll do:**
1. Install dependencies: `pip install -r requirements.txt`
2. Update `.env` with JWT secret
3. Test the endpoints
4. Tell me if anything doesn't work

---

## 📝 Quick Reference: SRS Modules vs Our Phases

| SRS Module | Our Phase | Priority | Status |
|------------|-----------|----------|--------|
| Module 1: User Registration & Auth | Phase 2 | CRITICAL | 🔄 80% |
| Module 2: Dashboard | Phase 13 (Frontend) | HIGH | ⏳ Pending |
| Module 3: Health Monitoring | Phase 3 | HIGH | ⏳ Pending |
| Module 4: Alertness & Fatigue | Phase 5 | HIGH | ⏳ Pending |
| Module 5: Readiness Assessment | Phase 7 | HIGH | ⏳ Pending |
| Module 6: Risk Prediction | Phase 6 (AI) | HIGH | ⏳ Pending |
| Module 7: Duty Management | Phase 8 | HIGH | ⏳ Pending |
| Module 8: Safety Reporting | Phase 10 | MEDIUM | ⏳ Pending |
| Module 9: Notifications | Phase 9 | MEDIUM | ⏳ Pending |
| Module 10: Compliance | Phase 11 | MEDIUM | ⏳ Pending |
| Module 11: Mobile App | Phase 14 | MEDIUM | ⏳ Pending |
| Module 12: System Admin | Phase 12 | CRITICAL | ⏳ Pending |
| Module 13: Security | Phase 12 | CRITICAL | ⏳ Pending |
| **Module 14: Alcohol & Substance** | **Phase 4** | **CRITICAL** | ⏳ **Next** |

---

## ✅ Next Immediate Actions

### Action 1: Complete RBAC (Right Now)
I'll create the permission system now, then you test it.

### Action 2: Test Everything
After I create RBAC, you:
1. Run: `uvicorn main:app --reload`
2. Test: Register → Login → Access protected endpoints
3. Test: Different roles (aviator, supervisor, etc.)

### Action 3: Move to Phase 3
Once auth is 100% working, we build the database schema for health records.

---

## 🎯 Success Criteria (From Your SRS)

Phase 2 is complete when:
- ✅ Users can register (SRS 1.1)
- ✅ Users can login with JWT (SRS 1.2)
- ✅ Passwords are hashed with bcrypt (SRS 1.2)
- ✅ RBAC is implemented (SRS 1.3)
- ✅ Sensitive endpoints are protected (SRS 1.3)
- ✅ All endpoints tested and working

---

**Ready to proceed?** I'll create the RBAC permission system now, following your SRS requirements exactly. Then you can test it in VS Code!

