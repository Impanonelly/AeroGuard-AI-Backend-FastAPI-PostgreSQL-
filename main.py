from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base

# ── Core routers (existing) ──────────────────────────────────────────────────
from routers import auth, dashboard
from routers import alcohol, health, duty, assessment, reports, notifications, substance, personnel, webauthn
from routers import medical_records
from routers import alertness
from routers import risk_prediction
from routers import frms
from routers import safety_analytics
from routers import compliance
from routers import user_management
from routers import audit_logs
from routers import security_settings
from routers import readiness
from routers import custom_api

# ── AI Engine ────────────────────────────────────────────────────────────────
from ai_engine.model import predict_risk as calculate_risk  # noqa: F401

# ── App Configuration ────────────────────────────────────────────────────────
app = FastAPI(
    title="AeroGuard AI — Aircrew Health & Alertness Monitoring System",
    description=(
        "AI-powered aviation safety platform for Akagera Aviation Ltd, Rwanda.\n\n"
        "Monitors aircrew health, fatigue, alertness, operational readiness, "
        "alcohol & substance compliance, and flight-duty safety.\n\n"
        "Aligned with RCAA operational safety requirements and ICAO standards.\n\n"
        "**AI role**: Predictive analysis and decision-support only. "
        "Human decision-making is preserved at all levels."
    ),
    version="2.0.0",
    contact={
        "name": "AeroGuard AI — Akagera Aviation Ltd",
        "url": "https://akageraaviation.com",
    },
    license_info={
        "name": "RCAA Certified Aviation Safety System",
    },
    openapi_tags=[
        {"name": "authentication",         "description": "JWT login, registration, token management"},
        {"name": "dashboard",              "description": "Role-aware KPI dashboards for all 5 roles"},
        {"name": "personnel-health",       "description": "Crew health vitals and physiological records"},
        {"name": "medical-records",        "description": "Confidential ICAO Class 1/2/3 medical certificates (Medical Officer only)"},
        {"name": "alertness-fatigue",      "description": "Real-time alertness scoring and fatigue trend analysis"},
        {"name": "readiness-assessment",   "description": "Manual aircrew readiness assessments with AI scoring and anomaly detection"},
        {"name": "alcohol-substance",      "description": "BAC screening and substance testing (RCAA zero-tolerance)"},
        {"name": "operational-readiness",  "description": "Fitness-for-duty assessment with AI-assisted scoring"},
        {"name": "flight-duty",            "description": "Flight duty period lifecycle with pre-flight safety gates"},
        {"name": "risk-prediction",        "description": "AI-powered fatigue risk prediction (decision-support only)"},
        {"name": "frms-monitoring",        "description": "Fatigue Risk Management System (ICAO Doc 9966)"},
        {"name": "safety-analytics",       "description": "Safety KPIs, incident reporting, and trend analysis"},
        {"name": "compliance",             "description": "RCAA regulatory compliance checks and violation tracking"},
        {"name": "notifications",          "description": "System alerts, warnings, and operational notifications"},
        {"name": "reports",                "description": "PDF and data report generation"},
        {"name": "user-management",        "description": "Administrator-level user CRUD and role assignment"},
        {"name": "audit-logs",             "description": "Immutable audit trail for all system actions"},
        {"name": "security-settings",      "description": "MFA, password management, and session security"},
        {"name": "biometric-security",     "description": "WebAuthn / hardware security key authentication"},
    ],
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# ── Create ALL database tables ───────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Register Routers ─────────────────────────────────────────────────────────

# Authentication
app.include_router(auth.router,              prefix="/auth",             tags=["authentication"])

# Dashboard (role-aware)
app.include_router(dashboard.router,         prefix="/dashboard",        tags=["dashboard"])

# Personnel Health
app.include_router(health.router,            prefix="/health",           tags=["personnel-health"])

# Medical Records (confidential)
app.include_router(medical_records.router,   prefix="/medical",          tags=["medical-records"])

# Alertness & Fatigue
app.include_router(alertness.router,         prefix="/alertness",        tags=["alertness-fatigue"])

# Readiness Assessment (Manual Web-Based)
app.include_router(readiness.router,         prefix="/readiness",        tags=["readiness-assessment"])

# Alcohol & Substance
app.include_router(alcohol.router,           prefix="/alcohol",          tags=["alcohol-substance"])
app.include_router(substance.router,         prefix="/substance",        tags=["alcohol-substance"])

# Operational Readiness
app.include_router(assessment.router,        prefix="/assessment",       tags=["operational-readiness"])

# Flight Duty
app.include_router(duty.router,              prefix="/duty",             tags=["flight-duty"])

# Risk Prediction (AI-assisted)
app.include_router(risk_prediction.router,   prefix="/risk",             tags=["risk-prediction"])

# FRMS Monitoring
app.include_router(frms.router,              prefix="/frms",             tags=["frms-monitoring"])

# Safety Analytics
app.include_router(safety_analytics.router,  prefix="/safety",           tags=["safety-analytics"])

# Compliance
app.include_router(compliance.router,        prefix="/compliance",       tags=["compliance"])

# Notifications
app.include_router(notifications.router,     prefix="/notifications",    tags=["notifications"])

# Reports
app.include_router(reports.router,           prefix="/reports",          tags=["reports"])

# Personnel (listing helpers)
app.include_router(personnel.router,         prefix="/personnel",        tags=["personnel-health"])

# User Management (admin)
app.include_router(user_management.router,   prefix="/users",            tags=["user-management"])

# Audit Logs
app.include_router(audit_logs.router,        prefix="/audit",            tags=["audit-logs"])

# Security Settings
app.include_router(security_settings.router, prefix="/security",         tags=["security-settings"])

# Biometric (WebAuthn)
app.include_router(webauthn.router,          prefix="/webauthn",         tags=["biometric-security"])

# Custom API endpoints for pilot/supervisor dashboards
app.include_router(custom_api.router,        prefix="",                  tags=["dashboard"])

# ── Root endpoints ───────────────────────────────────────────────────────────

@app.get("/", tags=["root"])
def read_root():
    return {
        "system": "AeroGuard AI — Aircrew Health & Alertness Monitoring System",
        "version": "2.0.0",
        "status": "operational",
        "operator": "Akagera Aviation Ltd, Rwanda",
        "regulatory_framework": "RCAA / ICAO Annex 1, 6, Doc 9966",
        "ai_role": "Decision-support only. Human authority is preserved.",
        "endpoints": "/docs",
        "modules": [
            "Dashboard", "Personnel Health", "Medical Records",
            "Alertness & Fatigue", "Readiness Assessment", "Alcohol & Substance", "Operational Readiness",
            "Flight Duty", "Risk Prediction", "FRMS Monitoring", "Safety Analytics",
            "Compliance", "Notifications", "Reports", "User Management",
            "Audit Logs", "Security Settings",
        ],
    }


@app.get("/health-check", tags=["root"])
def health_check():
    return {
        "status": "healthy",
        "service": "AeroGuard AI Backend",
        "version": "2.0.0",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }