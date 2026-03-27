# AeroGuard AI - Development Roadmap

## Overview
This document breaks down the complete SRS requirements into actionable development steps, organized by priority and dependencies. Each step is designed to be implemented, tested, and validated before moving to the next.

---

## Phase 1: Foundation & Core Backend ✅ COMPLETE
**Status**: Already implemented

### Completed Tasks:
- ✅ Python 3.14 + FastAPI + Uvicorn setup
- ✅ PostgreSQL 16 database connection
- ✅ Basic Pilot model and database schema
- ✅ Simple risk calculation algorithm
- ✅ Basic API endpoints (GET /, POST /assess/, GET /pilots/)

---

## Phase 2: Authentication & User Management
**Priority**: CRITICAL | **Estimated Time**: 1-2 weeks

### Step 2.1: User Model & Database Schema
**Dependencies**: Phase 1
**Tasks**:
1. Create `User` model with fields:
   - id, email, password_hash, full_name, employee_id
   - role (aviator, supervisor, safety_officer, administrator)
   - license_number, certification_details
   - is_active, created_at, updated_at
   - mfa_enabled, mfa_secret
   - last_login, session_timeout
2. Create `UserRole` enum/table for RBAC
3. Create database migration script
4. Update `models.py` with User model

**Deliverables**:
- `models.py` with User model
- Database migration script
- User table created in PostgreSQL

---

### Step 2.2: Password Security & Hashing
**Dependencies**: Step 2.1
**Tasks**:
1. Install `passlib[bcrypt]` and `python-jose[cryptography]`
2. Create `auth/utils.py` with:
   - `hash_password()` function using bcrypt (12 rounds)
   - `verify_password()` function
   - Password strength validation
3. Create password reset token generation
4. Add password requirements validation

**Deliverables**:
- `auth/utils.py` with password utilities
- Updated `requirements.txt`

---

### Step 2.3: JWT Authentication System
**Dependencies**: Step 2.2
**Tasks**:
1. Create `auth/jwt_handler.py`:
   - Generate JWT access tokens (15 min expiry)
   - Generate JWT refresh tokens (7 days expiry)
   - Token validation and decoding
   - Token refresh endpoint
2. Create `auth/dependencies.py`:
   - `get_current_user()` dependency
   - `get_current_active_user()` dependency
   - Role-based permission decorators
3. Create JWT secret key management in `.env`

**Deliverables**:
- `auth/jwt_handler.py`
- `auth/dependencies.py`
- JWT token generation and validation working

---

### Step 2.4: User Registration Endpoint
**Dependencies**: Step 2.3
**Tasks**:
1. Create `schemas/auth.py`:
   - `UserRegister` schema
   - `UserLogin` schema
   - `UserResponse` schema
   - `TokenResponse` schema
2. Create `routers/auth.py`:
   - `POST /auth/register` - User registration
   - Employee ID validation against Akagera Aviation records (mock for now)
   - Email uniqueness validation
   - Role assignment validation
3. Integrate with main app
4. Add input validation and error handling

**Deliverables**:
- `routers/auth.py` with registration endpoint
- `schemas/auth.py` with auth schemas
- Registration API tested and working

---

### Step 2.5: User Login & Token Management
**Dependencies**: Step 2.4
**Tasks**:
1. Implement `POST /auth/login`:
   - Email/password authentication
   - JWT token generation
   - Session tracking
   - Failed login attempt logging
2. Implement `POST /auth/refresh`:
   - Refresh token validation
   - New access token generation
3. Implement `POST /auth/logout`:
   - Token blacklisting (use Redis or database)
   - Session cleanup
4. Add rate limiting for login attempts

**Deliverables**:
- Login endpoint working
- Token refresh working
- Logout functionality

---

### Step 2.6: Role-Based Access Control (RBAC)
**Dependencies**: Step 2.5
**Tasks**:
1. Create `auth/permissions.py`:
   - Permission matrix for each role
   - Permission decorators:
     - `require_role(role)`
     - `require_permission(permission)`
     - `require_any_role(roles)`
2. Create permission constants:
   - VIEW_DASHBOARD, VIEW_PILOTS, ASSESS_PILOT
   - VIEW_REPORTS, MANAGE_USERS, OVERRIDE_ASSESSMENT
   - VIEW_SUBSTANCE_RECORDS, MANAGE_SYSTEM
3. Apply RBAC to existing endpoints
4. Test permission enforcement

**Deliverables**:
- `auth/permissions.py` with RBAC system
- All endpoints protected with appropriate permissions
- Permission testing completed

---

### Step 2.7: Multi-Factor Authentication (MFA)
**Dependencies**: Step 2.6
**Tasks**:
1. Install `pyotp` for TOTP generation
2. Create `auth/mfa.py`:
   - Generate MFA secret
   - Generate QR code for authenticator apps
   - Verify TOTP codes
3. Create endpoints:
   - `POST /auth/mfa/setup` - Enable MFA
   - `POST /auth/mfa/verify` - Verify MFA code
   - `POST /auth/mfa/disable` - Disable MFA
4. Update login flow to require MFA for supervisor/safety_officer/admin
5. Store MFA secrets encrypted

**Deliverables**:
- MFA setup and verification working
- MFA required for privileged roles
- QR code generation for authenticator apps

---

## Phase 3: Complete Database Schema
**Priority**: HIGH | **Estimated Time**: 1-2 weeks

### Step 3.1: Health Records Model
**Dependencies**: Phase 2
**Tasks**:
1. Create `HealthRecord` model:
   - id, user_id (FK), record_date, record_time
   - sleep_hours, stress_level, heart_rate, blood_pressure
   - alcohol_bac, substance_status, substance_test_date
   - reaction_score, alertness_score
   - created_at, created_by
2. Create `SubstanceScreening` model:
   - id, user_id (FK), screening_date, screening_time
   - screening_type (pre-flight, post-flight, random, scheduled)
   - result_status (cleared, flagged, pending)
   - substance_categories (cannabis, opioids, cocaine, etc.)
   - laboratory_result_pdf_path
   - supervising_officer_id, notes
3. Create relationships between User and HealthRecord
4. Create database migration

**Deliverables**:
- `models.py` with HealthRecord and SubstanceScreening models
- Database tables created
- Relationships established

---

### Step 3.2: Duty Management Models
**Dependencies**: Step 3.1
**Tasks**:
1. Create `DutyPeriod` model:
   - id, user_id (FK), duty_start, duty_end
   - flight_number, aircraft_type, route
   - duty_type (flight, standby, training)
   - rest_period_before, rest_period_after
   - alcohol_screening_completed, substance_screening_completed
   - status (scheduled, active, completed, cancelled)
2. Create `RestPeriod` model:
   - id, user_id (FK), rest_start, rest_end
   - rest_type (daily, weekly, extended)
   - minimum_required_hours, actual_hours
   - compliance_status
3. Create `FlightTimeLimit` model:
   - id, user_id (FK), period_type (daily, weekly, monthly)
   - limit_hours, current_hours, remaining_hours
   - last_reset_date
4. Create database migration

**Deliverables**:
- Duty management models created
- Database tables and relationships

---

### Step 3.3: Assessment & Readiness Models
**Dependencies**: Step 3.2
**Tasks**:
1. Create `FitnessAssessment` model:
   - id, user_id (FK), assessment_date, assessment_time
   - alertness_score, fatigue_score, risk_level
   - alcohol_bac, substance_status
   - readiness_status (fit, fit_with_monitoring, unfit)
   - ai_confidence_score, supervisor_override
   - override_justification, override_by_user_id
   - readiness_certificate_path
2. Create `RiskPrediction` model:
   - id, user_id (FK), prediction_date
   - risk_level (low, medium, high)
   - risk_score, risk_factors
   - ai_model_version, confidence_score
   - predicted_by_model
3. Create `CrewPairing` model:
   - id, flight_id, crew_member_1_id, crew_member_2_id
   - compatibility_score, risk_aggregation
   - pairing_date, status
4. Create database migration

**Deliverables**:
- Assessment models created
- Database schema complete

---

### Step 3.4: Notification & Alert Models
**Dependencies**: Step 3.3
**Tasks**:
1. Create `Notification` model:
   - id, user_id (FK), notification_type
   - title, message, priority (low, medium, high, critical)
   - channel (in-app, email, sms, push)
   - status (unread, read, acknowledged)
   - created_at, read_at, acknowledged_at
   - action_required, action_taken
2. Create `Alert` model:
   - id, alert_type, severity
   - title, description, affected_user_id
   - triggered_by_event, escalation_level
   - status (active, acknowledged, resolved)
   - created_at, resolved_at, resolved_by
3. Create `AlertHistory` model for audit trail
4. Create database migration

**Deliverables**:
- Notification and alert models
- Database tables created

---

### Step 3.5: Compliance & Audit Models
**Dependencies**: Step 3.4
**Tasks**:
1. Create `ComplianceRecord` model:
   - id, user_id (FK), compliance_type
   - requirement_name, requirement_standard (ICAO, Rwanda CAA)
   - status (compliant, non-compliant, pending)
   - expiry_date, last_verified_date
   - verification_document_path
2. Create `AuditLog` model:
   - id, user_id, action_type, resource_type
   - resource_id, action_details, ip_address
   - user_agent, timestamp, success
   - error_message (if failed)
3. Create `License` model:
   - id, user_id (FK), license_type, license_number
   - issue_date, expiry_date, issuing_authority
   - status (active, expired, suspended, revoked)
   - renewal_reminder_sent
4. Create database migration

**Deliverables**:
- Compliance and audit models
- Complete database schema

---

## Phase 4: Alcohol & Substance Monitoring Module
**Priority**: CRITICAL | **Estimated Time**: 1-2 weeks

### Step 4.1: Alcohol Screening Data Models
**Dependencies**: Phase 3
**Tasks**:
1. Create `AlcoholScreening` model:
   - id, user_id (FK), screening_date, screening_time
   - screening_type (pre-flight, post-flight, random)
   - bac_level (0.00 to 1.00)
   - testing_method, device_serial_number
   - supervising_officer_id, test_location
   - result_status (clear, warning, grounded)
   - violation_recorded, violation_details
   - created_at, created_by
2. Add alcohol screening status to User model
3. Create database migration
4. Add validation: BAC > 0.04% = automatic grounding

**Deliverables**:
- AlcoholScreening model
- Database table created
- Validation logic implemented

---

### Step 4.2: Pre-Flight Alcohol Screening Endpoint
**Dependencies**: Step 4.1
**Tasks**:
1. Create `schemas/alcohol.py`:
   - `AlcoholScreeningCreate` schema
   - `AlcoholScreeningResponse` schema
   - BAC validation (0.00 to 1.00)
2. Create `routers/alcohol.py`:
   - `POST /alcohol/pre-flight` - Record pre-flight BAC
   - Validate BAC threshold (0.04% max per ICAO)
   - Automatic grounding if BAC > 0.04%
   - Link to duty period
   - Trigger critical alert if violation
3. Create `services/alcohol_service.py`:
   - `record_alcohol_screening()` function
   - `check_bac_compliance()` function
   - `trigger_violation_alert()` function
4. Integrate with duty activation workflow

**Deliverables**:
- Pre-flight alcohol screening endpoint
- Automatic grounding logic
- Critical alert triggering

---

### Step 4.3: Post-Flight Alcohol Screening
**Dependencies**: Step 4.2
**Tasks**:
1. Create `POST /alcohol/post-flight` endpoint
2. Implement post-flight BAC recording
3. Flag any BAC > 0.00% as safety incident
4. Link to flight duty record
5. Auto-notify Safety Officer and Administrator
6. Create incident report automatically

**Deliverables**:
- Post-flight screening endpoint
- Incident flagging logic
- Notification system integration

---

### Step 4.4: Substance Screening Endpoints
**Dependencies**: Step 4.3
**Tasks**:
1. Create `schemas/substance.py`:
   - `SubstanceScreeningCreate` schema
   - `SubstanceScreeningResponse` schema
   - Substance categories enum
2. Create `routers/substance.py`:
   - `POST /substance/record` - Record substance test
   - `POST /substance/import-lab-result` - Import PDF lab results
   - `GET /substance/{user_id}/history` - Get screening history
   - `GET /substance/pending` - Get pending confirmations
3. Implement status workflow:
   - Cleared → Allow duty
   - Flagged → Block duty, trigger alert
   - Pending → Block duty until cleared
4. Add PDF upload and storage (local or S3)

**Deliverables**:
- Substance screening endpoints
- Status workflow enforcement
- PDF import functionality

---

### Step 4.5: Violation Management System
**Dependencies**: Step 4.4
**Tasks**:
1. Create `Violation` model:
   - id, user_id (FK), violation_type (alcohol, substance)
   - violation_date, violation_time
   - bac_level (if alcohol), substance_detected
   - supervising_officer_id, corrective_action
   - status (recorded, under_investigation, resolved)
   - suspension_applied, suspension_end_date
2. Create `routers/violations.py`:
   - `GET /violations` - List all violations
   - `GET /violations/{user_id}` - User violation history
   - `POST /violations/{violation_id}/suspend` - Suspend user
   - `GET /violations/rolling-12-months` - Check 12-month count
3. Implement automatic flagging:
   - 2+ violations in 12 months = warning flag
   - Automatic suspension workflow
4. Create violation reports

**Deliverables**:
- Violation management system
- Automatic flagging logic
- Suspension workflow

---

### Step 4.6: Mandatory Screening Workflow
**Dependencies**: Step 4.5
**Tasks**:
1. Create `services/screening_workflow.py`:
   - `check_preflight_requirements()` function
   - `validate_screening_completion()` function
   - `block_duty_if_incomplete()` function
2. Integrate with duty activation:
   - Step 1: Check alcohol BAC completed
   - Step 2: Check substance status is Cleared
   - Step 3: Both passed → allow fitness assessment
   - Any failure → block duty activation
3. Create supervisor checklist endpoint
4. Add screening completion validation to readiness assessment

**Deliverables**:
- Mandatory screening workflow
- Duty activation blocking logic
- Supervisor checklist

---

## Phase 5: Enhanced Alertness & Risk Calculation
**Priority**: HIGH | **Estimated Time**: 1-2 weeks

### Step 5.1: Advanced Alertness Scoring Algorithm
**Dependencies**: Phase 4
**Tasks**:
1. Create `services/alertness_calculator.py`:
   - Implement weighted 5-factor algorithm:
     - Sleep hours (30% weight)
     - Duty duration (25% weight)
     - Stress level (20% weight)
     - Reaction time test (15% weight)
     - Circadian factor (10% weight)
   - Alcohol BAC override logic (any BAC > 0.00% = Red/Unfit)
   - Substance status override (Flagged/Pending = Red/Unfit)
2. Create `services/circadian_calculator.py`:
   - Calculate circadian rhythm impact
   - Time-of-day adjustment
   - Historical shift pattern analysis
3. Update risk calculation in `main.py` to use new algorithm
4. Add AI confidence scoring placeholder

**Deliverables**:
- Advanced alertness scoring algorithm
- Circadian factor calculation
- Override logic for alcohol/substance

---

### Step 5.2: Fatigue Accumulation Modeling
**Dependencies**: Step 5.1
**Tasks**:
1. Create `services/fatigue_model.py`:
   - Calculate fatigue accumulation over time
   - Consider duty history, rest periods, sleep patterns
   - Implement ICAO FRMS fatigue modeling
2. Create `FatigueHistory` model to track accumulation
3. Create endpoint `GET /fatigue/{user_id}/accumulation`
4. Add fatigue trend analysis
5. Generate fatigue warnings

**Deliverables**:
- Fatigue accumulation model
- Fatigue history tracking
- Trend analysis

---

### Step 5.3: Enhanced Risk Prediction
**Dependencies**: Step 5.2
**Tasks**:
1. Create `services/risk_predictor.py`:
   - Individual risk scoring (Low/Medium/High)
   - Crew-level risk aggregation
   - Pattern recognition for recurring risks
2. Update risk calculation to include:
   - Alcohol/substance violation history
   - Long-term risk factors
   - Historical pattern analysis
3. Create `POST /predict/risk` endpoint
4. Add early warning system for High Risk personnel
5. Implement crew pairing compatibility check

**Deliverables**:
- Enhanced risk prediction
- Crew-level aggregation
- Early warning system

---

## Phase 6: AI/ML Model Integration
**Priority**: HIGH | **Estimated Time**: 2-3 weeks

### Step 6.1: ML Model Setup & Dependencies
**Dependencies**: Phase 5
**Tasks**:
1. Update `requirements.txt`:
   - scikit-learn
   - tensorflow (or pytorch)
   - pandas, numpy
   - SHAP (for explainability)
2. Create `ai/` directory structure:
   - `ai/models/` - Trained model files
   - `ai/training/` - Training scripts
   - `ai/prediction/` - Prediction services
3. Create `ai/config.py` for model configuration
4. Set up model versioning system

**Deliverables**:
- AI dependencies installed
- Directory structure created
- Configuration setup

---

### Step 6.2: Fatigue Prediction Model
**Dependencies**: Step 6.1
**Tasks**:
1. Create `ai/training/fatigue_model.py`:
   - Data preprocessing pipeline
   - Feature engineering (sleep, duty, stress, etc.)
   - Random Forest model training
   - Model evaluation and validation
   - Model serialization (pickle/joblib)
2. Create training dataset from historical health records
3. Train initial model (can use synthetic data for MVP)
4. Create `ai/prediction/fatigue_predictor.py`:
   - Load trained model
   - Preprocess input data
   - Generate fatigue score (0-100)
   - Return confidence rating
5. Integrate with alertness scoring

**Deliverables**:
- Trained fatigue prediction model
- Prediction service
- Integration with alertness system

---

### Step 6.3: Risk Classification Model
**Dependencies**: Step 6.2
**Tasks**:
1. Create `ai/training/risk_classifier.py`:
   - Gradient Boosting classifier
   - Feature selection for risk factors
   - Train on labeled risk data (Low/Medium/High)
   - Model evaluation metrics
2. Create `ai/prediction/risk_classifier.py`:
   - Load trained model
   - Predict risk level
   - Return probability distribution
   - SHAP explainability integration
3. Create `POST /ai/predict/risk` endpoint
4. Add AI confidence scores to responses
5. Implement model version tracking

**Deliverables**:
- Risk classification model
- SHAP explainability
- API endpoint for risk prediction

---

### Step 6.4: Pattern Recognition Model
**Dependencies**: Step 6.3
**Tasks**:
1. Create `ai/training/pattern_recognition.py`:
   - Logistic regression for trend identification
   - Time series analysis for recurring patterns
   - Anomaly detection
2. Create `ai/prediction/pattern_analyzer.py`:
   - Identify fatigue trends
   - Detect recurring risk patterns
   - Generate pattern alerts
3. Create `GET /ai/patterns/{user_id}` endpoint
4. Integrate pattern alerts with notification system

**Deliverables**:
- Pattern recognition model
- Trend analysis
- Pattern alert system

---

## Phase 7: Operational Readiness Assessment
**Priority**: HIGH | **Estimated Time**: 1 week

### Step 7.1: Fitness-for-Duty Assessment Endpoint
**Dependencies**: Phase 6
**Tasks**:
1. Create `schemas/readiness.py`:
   - `ReadinessAssessment` schema
   - `ReadinessResponse` schema
   - `ReadinessCertificate` schema
2. Create `services/readiness_assessor.py`:
   - Combine AI scoring, health data, alcohol/substance status
   - Classify: Fit, Fit with Monitoring, Unfit
   - Block clearance if BAC > 0.04% or substance Flagged
   - Generate readiness certificate
3. Create `POST /readiness/assess` endpoint
4. Add supervisor review workflow
5. Generate digital readiness certificates (PDF)

**Deliverables**:
- Fitness-for-duty assessment endpoint
- Readiness classification logic
- Certificate generation

---

### Step 7.2: Supervisor Override System
**Dependencies**: Step 7.1
**Tasks**:
1. Create `POST /readiness/{assessment_id}/override` endpoint
2. Implement override logic:
   - Supervisor can override AI decision
   - Require written justification
   - Log override in audit trail
   - Cannot override BAC/substance blocks
3. Create override history tracking
4. Add override notifications
5. Generate override reports

**Deliverables**:
- Supervisor override system
- Override logging and audit trail
- Justification requirement

---

### Step 7.3: Crew Pairing Compatibility
**Dependencies**: Step 7.2
**Tasks**:
1. Create `services/crew_pairing.py`:
   - Analyze individual risk levels
   - Calculate crew compatibility score
   - Prevent High Risk + High Risk pairings
   - Suggest optimal crew combinations
2. Create `POST /crew/pairing/analyze` endpoint
3. Create `GET /crew/pairing/suggestions` endpoint
4. Add crew pairing validation to flight assignment

**Deliverables**:
- Crew pairing analysis
- Compatibility scoring
- Pairing suggestions

---

## Phase 8: Duty Management System
**Priority**: HIGH | **Estimated Time**: 1-2 weeks

### Step 8.1: Duty Period Tracking
**Dependencies**: Phase 7
**Tasks**:
1. Create `schemas/duty.py`:
   - `DutyPeriodCreate` schema
   - `DutyPeriodResponse` schema
   - `RestPeriod` schema
2. Create `routers/duty.py`:
   - `POST /duty/start` - Start duty period (requires screening)
   - `POST /duty/end` - End duty period
   - `GET /duty/{user_id}/current` - Get current duty
   - `GET /duty/{user_id}/history` - Get duty history
3. Implement duty activation blocking:
   - Check alcohol screening completed
   - Check substance status cleared
   - Block if requirements not met
4. Link duty periods to flights

**Deliverables**:
- Duty period tracking endpoints
- Activation blocking logic
- Duty history tracking

---

### Step 8.2: ICAO Compliance & Flight Time Limits
**Dependencies**: Step 8.1
**Tasks**:
1. Create `services/icao_compliance.py`:
   - Implement ICAO Annex 6 flight time limits
   - Daily, weekly, monthly limit tracking
   - Rest period requirement calculation
   - Compliance validation
2. Create `routers/compliance.py`:
   - `GET /compliance/{user_id}/flight-time` - Check flight time
   - `GET /compliance/{user_id}/rest-deficiency` - Check rest
   - `POST /compliance/validate` - Validate compliance
3. Create alerts for approaching limits
4. Block duty if limits exceeded
5. Generate compliance reports

**Deliverables**:
- ICAO compliance checking
- Flight time limit tracking
- Rest deficiency alerts

---

### Step 8.3: Fatigue-Based Scheduling
**Dependencies**: Step 8.2
**Tasks**:
1. Create `services/scheduling_optimizer.py`:
   - Analyze duty patterns for fatigue risk
   - Suggest schedule optimizations
   - Consider circadian rhythms
   - Minimize fatigue accumulation
2. Create `POST /scheduling/optimize` endpoint
3. Create `GET /scheduling/suggestions` endpoint
4. Integrate with duty assignment system

**Deliverables**:
- Scheduling optimization service
- Fatigue-based suggestions
- Integration with duty system

---

## Phase 9: Notification & Alert System
**Priority**: MEDIUM | **Estimated Time**: 1 week

### Step 9.1: Notification Service Infrastructure
**Dependencies**: Phase 8
**Tasks**:
1. Install notification libraries:
   - `celery` for async tasks
   - `redis` for task queue
   - `sendgrid` or `smtplib` for email
   - `twilio` for SMS (optional)
2. Create `services/notification_service.py`:
   - Send in-app notifications
   - Send email notifications
   - Send SMS notifications (optional)
   - Multi-channel notification support
3. Create `services/alert_service.py`:
   - Generate alerts based on triggers
   - Escalation logic
   - Alert priority management
4. Set up Celery workers and Redis

**Deliverables**:
- Notification service infrastructure
- Multi-channel support
- Alert generation system

---

### Step 9.2: Critical Alert Implementation
**Dependencies**: Step 9.1
**Tasks**:
1. Implement critical alerts for:
   - BAC > 0.04% violation
   - Substance test Flagged
   - High Risk personnel classification
   - Flight time limit exceeded
   - Rest deficiency
2. Create escalation workflow:
   - Immediate notification to Supervisor
   - Escalate to Safety Officer if not acknowledged
   - Escalate to Administrator if critical
3. Create `POST /alerts/critical` endpoint
4. Implement alert acknowledgment system
5. Create alert history tracking

**Deliverables**:
- Critical alert system
- Escalation workflow
- Alert acknowledgment

---

### Step 9.3: Proactive Reminders
**Dependencies**: Step 9.2
**Tasks**:
1. Create scheduled tasks (Celery beat):
   - Health assessment reminders
   - Duty limit approaching alerts
   - License renewal reminders (30 days before)
   - Screening completion reminders
2. Create `services/reminder_service.py`
3. Configure reminder schedules
4. Test reminder delivery

**Deliverables**:
- Proactive reminder system
- Scheduled task configuration
- Reminder testing

---

## Phase 10: Reporting & Analytics
**Priority**: MEDIUM | **Estimated Time**: 1-2 weeks

### Step 10.1: Safety Reporting Infrastructure
**Dependencies**: Phase 9
**Tasks**:
1. Install reporting libraries:
   - `reportlab` for PDF generation
   - `openpyxl` for Excel generation
   - `jinja2` for template rendering
2. Create `services/report_generator.py`:
   - PDF report generation
   - Excel report generation
   - Template system
   - Data aggregation
3. Create `templates/reports/` directory
4. Set up report storage (local or S3)

**Deliverables**:
- Report generation infrastructure
- PDF and Excel support
- Template system

---

### Step 10.2: Operational Safety Reports
**Dependencies**: Step 10.1
**Tasks**:
1. Create `routers/reports.py`:
   - `GET /reports/safety/{period}` - Safety report
   - `GET /reports/fatigue/{period}` - Fatigue report
   - `GET /reports/incidents/{period}` - Incident report
2. Implement report data aggregation:
   - Fatigue-related incidents
   - Near-miss reports
   - Duty violations
   - Risk trend analysis
3. Create report templates
4. Add date range filtering
5. Generate PDF and Excel formats

**Deliverables**:
- Safety report endpoints
- Report templates
- Data aggregation logic

---

### Step 10.3: Alcohol & Substance Compliance Reports
**Dependencies**: Step 10.2
**Tasks**:
1. Create `GET /reports/substance-compliance/{period}` endpoint
2. Generate compliance report with:
   - Total screenings conducted
   - Pass rate percentage
   - Violation count
   - Flagged personnel list
   - Pending results summary
3. Create anonymized version for CAA submission
4. Include screening event details:
   - Date, time, result, BAC value
   - Personnel ID (anonymized in export)
   - Supervising officer
5. Generate monthly compliance summary
6. Track 12-month violation patterns

**Deliverables**:
- Substance compliance reports
- Anonymized CAA reports
- Monthly summaries

---

### Step 10.4: Risk Analytics Dashboard Data
**Dependencies**: Step 10.3
**Tasks**:
1. Create analytics endpoints:
   - `GET /analytics/risk-distribution` - Risk level distribution
   - `GET /analytics/fatigue-trends` - Fatigue trends over time
   - `GET /analytics/compliance-rates` - Compliance metrics
   - `GET /analytics/crew-readiness` - Crew readiness stats
2. Implement data aggregation for charts
3. Create time-series data endpoints
4. Add filtering and date range support
5. Optimize queries for performance

**Deliverables**:
- Analytics endpoints
- Data aggregation for dashboards
- Performance optimization

---

## Phase 11: Compliance Management
**Priority**: MEDIUM | **Estimated Time**: 1 week

### Step 11.1: Regulatory Standards Tracking
**Dependencies**: Phase 10
**Tasks**:
1. Create `services/compliance_tracker.py`:
   - Track ICAO Annex 6 requirements
   - Track ICAO Doc 9654 (BAC limits)
   - Track Rwanda CAA regulations
   - Track ICAO FRMS guidelines
2. Create compliance validation functions
3. Create `GET /compliance/standards` endpoint
4. Implement compliance gap analysis
5. Generate compliance status reports

**Deliverables**:
- Compliance tracking service
- Regulatory standards validation
- Gap analysis

---

### Step 11.2: License & Certification Management
**Dependencies**: Step 11.1
**Tasks**:
1. Create `routers/licenses.py`:
   - `POST /licenses` - Add license
   - `GET /licenses/{user_id}` - Get user licenses
   - `PUT /licenses/{license_id}` - Update license
   - `GET /licenses/expiring` - Get expiring licenses
2. Implement expiry tracking
3. Create 30-day renewal reminders
4. Add license status management
5. Link licenses to compliance records

**Deliverables**:
- License management endpoints
- Expiry tracking
- Renewal reminders

---

### Step 11.3: Audit & Compliance Documentation
**Dependencies**: Step 11.2
**Tasks**:
1. Create `routers/audit.py`:
   - `GET /audit/logs` - Get audit logs
   - `GET /audit/compliance-export` - Export compliance data
   - `GET /audit/substance-records` - Export substance records
2. Implement audit log querying
3. Create compliance documentation generator
4. Add data retention policy enforcement
5. Create export functionality for inspections

**Deliverables**:
- Audit log endpoints
- Compliance documentation
- Export functionality

---

## Phase 12: Security Hardening
**Priority**: CRITICAL | **Estimated Time**: 1 week

### Step 12.1: Data Encryption
**Dependencies**: Phase 11
**Tasks**:
1. Create `services/encryption.py`:
   - AES-256 encryption for sensitive data
   - Encrypt alcohol/substance records
   - Encrypt health data at rest
   - Key management system
2. Implement field-level encryption for:
   - Health records
   - Substance screening results
   - Violation records
3. Add decryption utilities
4. Test encryption/decryption performance

**Deliverables**:
- Data encryption service
- Field-level encryption
- Key management

---

### Step 12.2: HTTPS & Transport Security
**Dependencies**: Step 12.1
**Tasks**:
1. Configure SSL/TLS certificates
2. Enforce HTTPS on all endpoints
3. Set up reverse proxy (nginx) if needed
4. Configure CORS properly
5. Add security headers
6. Test SSL configuration

**Deliverables**:
- HTTPS enforcement
- SSL/TLS configuration
- Security headers

---

### Step 12.3: Access Control for Sensitive Data
**Dependencies**: Step 12.2
**Tasks**:
1. Implement strict access control for:
   - Alcohol/substance records (only tested person, supervisor, safety officer, admin)
   - Health data (role-based restrictions)
   - Violation records (limited access)
2. Create access logging for sensitive data
3. Implement data anonymization for exports
4. Add consent management system
5. Test access control enforcement

**Deliverables**:
- Strict access control
- Access logging
- Data anonymization

---

### Step 12.4: Audit Logging Enhancement
**Dependencies**: Step 12.3
**Tasks**:
1. Enhance audit logging:
   - Log all data access
   - Log all modifications
   - Log all exports
   - Log login/logout events
   - Log permission changes
2. Create immutable audit log storage
3. Implement tamper-evident logging
4. Add audit log querying and reporting
5. Test audit log integrity

**Deliverables**:
- Enhanced audit logging
- Immutable log storage
- Audit reporting

---

## Phase 13: Frontend - React.js Web Application
**Priority**: HIGH | **Estimated Time**: 3-4 weeks

### Step 13.1: React Project Setup
**Dependencies**: Phase 12
**Tasks**:
1. Create React app with Vite or Create React App
2. Install dependencies:
   - react-router-dom
   - redux toolkit
   - axios
   - react-hook-form
   - tailwindcss
   - recharts
   - chart.js
3. Set up project structure
4. Configure Tailwind CSS
5. Set up API client with axios
6. Configure Redux store

**Deliverables**:
- React project created
- Dependencies installed
- Project structure set up

---

### Step 13.2: Authentication & Routing
**Dependencies**: Step 13.1
**Tasks**:
1. Create authentication pages:
   - Login page
   - Register page
   - MFA setup page
   - MFA verification page
2. Implement JWT token management:
   - Store tokens in secure storage
   - Token refresh logic
   - Auto-logout on expiry
3. Create protected route components
4. Implement role-based route access
5. Create navigation components
6. Test authentication flow

**Deliverables**:
- Authentication pages
- Protected routes
- Role-based access

---

### Step 13.3: Aviator Dashboard
**Dependencies**: Step 13.2
**Tasks**:
1. Create aviator dashboard components:
   - Personal alertness score display
   - Pre-flight checklist
   - Sleep log summary
   - Duty schedule view
   - Fatigue self-report form
2. Implement real-time score updates
3. Create color-coded status indicators
4. Add pre-flight assessment form
5. Integrate with backend API
6. Test dashboard functionality

**Deliverables**:
- Aviator dashboard
- Pre-flight checklist
- Assessment forms

---

### Step 13.4: Supervisor Dashboard
**Dependencies**: Step 13.3
**Tasks**:
1. Create supervisor dashboard:
   - Full crew readiness overview
   - Risk alert summary
   - Pending assessment actions
   - Alcohol/substance screening status per crew
   - Override functionality
2. Implement crew status cards
3. Create assessment review interface
4. Add override justification form
5. Create screening status indicators
6. Test supervisor workflows

**Deliverables**:
- Supervisor dashboard
- Crew overview
- Override system

---

### Step 13.5: Safety Officer Dashboard
**Dependencies**: Step 13.4
**Tasks**:
1. Create safety officer dashboard:
   - Safety performance indicators
   - Incident trends charts
   - Compliance rates
   - Risk analytics
2. Implement data visualization:
   - Line charts for trends
   - Bar charts for comparisons
   - Pie charts for distribution
   - Radar charts for multi-factor analysis
3. Create report generation interface
4. Add filtering and date range selection
5. Test analytics dashboard

**Deliverables**:
- Safety officer dashboard
- Data visualization
- Analytics interface

---

### Step 13.6: Administrator Dashboard
**Dependencies**: Step 13.5
**Tasks**:
1. Create administrator dashboard:
   - System health monitoring
   - User activity summary
   - Backup status
   - Audit log highlights
   - User management interface
2. Create user management components:
   - User list
   - User creation/edit forms
   - Role assignment
   - Suspension workflow
3. Create system configuration panel
4. Add alcohol/substance administration panel
5. Test admin functionality

**Deliverables**:
- Administrator dashboard
- User management
- System configuration

---

### Step 13.7: Alcohol & Substance Management UI
**Dependencies**: Step 13.6
**Tasks**:
1. Create alcohol screening interface:
   - Pre-flight BAC entry form
   - Post-flight BAC entry form
   - Screening history view
   - Violation display
2. Create substance screening interface:
   - Screening result entry
   - Lab result import (PDF upload)
   - Screening status display
   - Pending confirmations list
3. Create supervisor checklist interface
4. Add violation management UI
5. Test screening workflows

**Deliverables**:
- Screening interfaces
- Violation management UI
- Supervisor checklist

---

## Phase 14: Mobile Application - Flutter
**Priority**: MEDIUM | **Estimated Time**: 2-3 weeks

### Step 14.1: Flutter Project Setup
**Dependencies**: Phase 13
**Tasks**:
1. Create Flutter project
2. Install dependencies:
   - dio (HTTP client)
   - shared_preferences (local storage)
   - sqflite (offline database)
   - local_auth (biometric auth)
   - firebase_messaging (push notifications)
   - encrypt (AES-256 encryption)
3. Set up project structure
4. Configure API client
5. Set up state management (Provider or Riverpod)

**Deliverables**:
- Flutter project created
- Dependencies installed
- Project structure

---

### Step 14.2: Authentication & Biometric Login
**Dependencies**: Step 14.1
**Tasks**:
1. Create login screen
2. Implement biometric authentication:
   - Fingerprint login
   - Face ID login
   - Fallback to password
3. Implement JWT token storage (encrypted)
4. Create registration flow
5. Implement MFA verification
6. Test biometric authentication

**Deliverables**:
- Biometric authentication
- Login/registration flows
- Token management

---

### Step 14.3: Offline Mode & Data Sync
**Dependencies**: Step 14.2
**Tasks**:
1. Set up SQLite database for offline storage
2. Implement offline data models
3. Create sync service:
   - Queue offline actions
   - Sync on reconnection
   - Conflict resolution
4. Implement offline pre-flight assessment
5. Add sync status indicator
6. Test offline functionality

**Deliverables**:
- Offline database
- Sync service
- Offline assessment capability

---

### Step 14.4: Pre-Flight Assessment Mobile UI
**Dependencies**: Step 14.3
**Tasks**:
1. Create pre-flight assessment screen:
   - Health data entry
   - Alcohol self-declaration checklist
   - Substance status display
   - Assessment submission
2. Implement offline assessment form
3. Add alcohol self-declaration step
4. Create assessment history view
5. Add push notification integration
6. Test mobile assessment flow

**Deliverables**:
- Pre-flight assessment UI
- Offline form support
- Push notifications

---

### Step 14.5: Mobile Dashboard & Notifications
**Dependencies**: Step 14.4
**Tasks**:
1. Create mobile dashboard:
   - Alertness score display
   - Risk level indicator
   - Upcoming duties
   - Recent assessments
2. Implement push notifications:
   - Risk alerts
   - Duty reminders
   - Critical alerts (alcohol/substance)
3. Create notification settings
4. Add notification history
5. Test notification delivery

**Deliverables**:
- Mobile dashboard
- Push notifications
- Notification management

---

## Phase 15: Testing & Quality Assurance
**Priority**: CRITICAL | **Estimated Time**: 2 weeks

### Step 15.1: Backend Unit Testing
**Dependencies**: Phase 14
**Tasks**:
1. Set up pytest testing framework
2. Create test database configuration
3. Write unit tests for:
   - Authentication functions
   - Risk calculation algorithms
   - Alertness scoring
   - AI model predictions
   - Screening workflows
4. Achieve 80%+ code coverage
5. Set up CI/CD for automated testing

**Deliverables**:
- Unit test suite
- Test coverage reports
- CI/CD pipeline

---

### Step 15.2: API Integration Testing
**Dependencies**: Step 15.1
**Tasks**:
1. Create API test suite using pytest
2. Test all endpoints:
   - Authentication endpoints
   - Assessment endpoints
   - Screening endpoints
   - Reporting endpoints
   - Admin endpoints
3. Test error handling
4. Test permission enforcement
5. Create Postman collection
6. Document API testing results

**Deliverables**:
- API test suite
- Postman collection
- Test documentation

---

### Step 15.3: Frontend Testing
**Dependencies**: Step 15.2
**Tasks**:
1. Set up Jest and React Testing Library
2. Write component tests
3. Write integration tests
4. Test user flows:
   - Login/registration
   - Assessment submission
   - Dashboard interactions
   - Override workflows
5. Test responsive design
6. Achieve 70%+ coverage

**Deliverables**:
- Frontend test suite
- Component tests
- Integration tests

---

### Step 15.4: End-to-End Testing
**Dependencies**: Step 15.3
**Tasks**:
1. Set up E2E testing (Cypress or Playwright)
2. Create E2E test scenarios:
   - Complete user registration flow
   - Pre-flight assessment workflow
   - Supervisor override workflow
   - Alcohol/substance screening flow
   - Report generation
3. Test cross-browser compatibility
4. Test mobile responsiveness
5. Document test results

**Deliverables**:
- E2E test suite
- Test scenarios
- Test documentation

---

## Phase 16: Deployment & DevOps
**Priority**: CRITICAL | **Estimated Time**: 1-2 weeks

### Step 16.1: Docker Containerization
**Dependencies**: Phase 15
**Tasks**:
1. Create Dockerfile for backend
2. Create Dockerfile for frontend
3. Create docker-compose.yml:
   - Backend service
   - Frontend service
   - PostgreSQL service
   - Redis service
4. Configure environment variables
5. Test container builds
6. Document Docker setup

**Deliverables**:
- Dockerfiles
- docker-compose.yml
- Container documentation

---

### Step 16.2: AWS Cloud Deployment
**Dependencies**: Step 16.1
**Tasks**:
1. Set up AWS account and services:
   - EC2 for backend
   - RDS for PostgreSQL
   - S3 for file storage
   - CloudFront for CDN (optional)
2. Configure security groups
3. Set up load balancer
4. Configure auto-scaling
5. Set up monitoring (CloudWatch)
6. Configure backups
7. Test deployment

**Deliverables**:
- AWS infrastructure
- Deployment configuration
- Monitoring setup

---

### Step 16.3: CI/CD Pipeline
**Dependencies**: Step 16.2
**Tasks**:
1. Set up GitHub Actions workflow:
   - Automated testing
   - Code linting
   - Security scanning
   - Automated deployment
2. Configure deployment stages:
   - Development
   - Staging
   - Production
3. Set up database migrations in CI/CD
4. Configure environment-specific configs
5. Test CI/CD pipeline

**Deliverables**:
- GitHub Actions workflow
- Automated deployment
- CI/CD documentation

---

### Step 16.4: Production Hardening
**Dependencies**: Step 16.3
**Tasks**:
1. Configure production environment variables
2. Set up SSL certificates
3. Configure firewall rules
4. Set up backup automation
5. Configure log aggregation
6. Set up error tracking (Sentry)
7. Performance optimization
8. Security audit
9. Load testing

**Deliverables**:
- Production environment
- Security hardening
- Performance optimization

---

## Implementation Priority Summary

### Critical Path (Must Complete First):
1. Phase 2: Authentication & User Management
2. Phase 3: Complete Database Schema
3. Phase 4: Alcohol & Substance Monitoring
4. Phase 5: Enhanced Alertness & Risk Calculation
5. Phase 12: Security Hardening
6. Phase 15: Testing
7. Phase 16: Deployment

### High Priority (Core Features):
- Phase 6: AI/ML Model Integration
- Phase 7: Operational Readiness Assessment
- Phase 8: Duty Management System
- Phase 13: React.js Frontend

### Medium Priority (Enhanced Features):
- Phase 9: Notification & Alert System
- Phase 10: Reporting & Analytics
- Phase 11: Compliance Management
- Phase 14: Flutter Mobile App

---

## Development Workflow Recommendations

1. **Sprint Planning**: Break each phase into 1-2 week sprints
2. **Daily Standups**: Track progress on current phase
3. **Code Reviews**: Review all code before merging
4. **Testing**: Write tests alongside features (TDD approach)
5. **Documentation**: Update docs as you build
6. **Version Control**: Use Git branches for each feature
7. **Incremental Deployment**: Deploy to staging frequently

---

## Next Immediate Steps

Based on current status (Phase 1 complete), start with:

1. **Week 1-2**: Phase 2 - Authentication & User Management
   - Step 2.1: User Model
   - Step 2.2: Password Security
   - Step 2.3: JWT Authentication

2. **Week 3-4**: Continue Phase 2
   - Step 2.4: User Registration
   - Step 2.5: Login & Token Management
   - Step 2.6: RBAC Implementation

3. **Week 5**: Phase 3 - Database Schema
   - Step 3.1: Health Records Model
   - Step 3.2: Duty Management Models

---

This roadmap provides a clear, step-by-step path from your current state to a fully functional AeroGuard AI system. Each step builds on the previous one, ensuring a solid foundation for your final year project.

