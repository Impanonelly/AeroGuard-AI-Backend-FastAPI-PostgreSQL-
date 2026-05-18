"""
seed_ui_demo_users.py
=====================
Inserts the 5 "Quick Demo Access" users shown on the AeroGuard login page.

Users:
  1. Emmanuel NIYONZIMA  – Administrator
  2. Grace MUTESI        – Safety Manager  (safety_officer)
  3. Dr. Jean HABIMANA   – Medical Officer (safety_officer)
  4. Sarah UWASE         – Supervisor
  5. Patrick MUGISHA     – Viewer          (aviator / read-only persona)

All users share the same demo password: Password123!
Run with:  python seed_ui_demo_users.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, UserRole
from auth.utils import hash_password

DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    {
        "email":       "emmanuel.niyonzima@aeroguard.com",
        "full_name":   "Emmanuel NIYONZIMA",
        "employee_id": "AKG-ADM-001",
        "role":        UserRole.ADMINISTRATOR,
        "license_number": None,
        "certification_details": "System Administrator – Full Access",
    },
    {
        "email":       "grace.mutesi@aeroguard.com",
        "full_name":   "Grace MUTESI",
        "employee_id": "AKG-SM-001",
        "role":        UserRole.SAFETY_OFFICER,
        "license_number": "RW-SO-001",
        "certification_details": "Safety Manager – RCAA Certified",
    },
    {
        "email":       "jean.habimana@aeroguard.com",
        "full_name":   "Dr. Jean HABIMANA",
        "employee_id": "AKG-MED-001",
        "role":        UserRole.SAFETY_OFFICER,   # closest backend role
        "license_number": "MED-RW-002",
        "certification_details": "Aviation Medical Officer – Class 1",
    },
    {
        "email":       "sarah.uwase@aeroguard.com",
        "full_name":   "Sarah UWASE",
        "employee_id": "AKG-SUP-001",
        "role":        UserRole.SUPERVISOR,
        "license_number": "RW-ATPL-SUP-01",
        "certification_details": "Flight Operations Supervisor",
    },
    {
        "email":       "patrick.mugisha@aeroguard.com",
        "full_name":   "Patrick MUGISHA",
        "employee_id": "AKG-VWR-001",
        "role":        UserRole.AVIATOR,           # viewer persona – read-only aviator
        "license_number": None,
        "certification_details": "Read-Only Observer Account",
    },
]


def seed():
    db = SessionLocal()
    created = []
    skipped = []

    try:
        for u in DEMO_USERS:
            existing = db.query(User).filter(
                (User.email == u["email"]) | (User.employee_id == u["employee_id"])
            ).first()

            if existing:
                skipped.append(u["full_name"])
                continue

            new_user = User(
                email=u["email"],
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=u["full_name"],
                employee_id=u["employee_id"],
                role=u["role"],
                license_number=u.get("license_number"),
                certification_details=u.get("certification_details"),
                is_active=True,
            )
            db.add(new_user)
            created.append(u["full_name"])

        db.commit()

        print("\n=== AeroGuard Demo User Seed ===")
        if created:
            print(f"✅ Created ({len(created)}):")
            for name in created:
                print(f"   • {name}")
        if skipped:
            print(f"⏭  Already existed ({len(skipped)}), skipped:")
            for name in skipped:
                print(f"   • {name}")
        print(f"\n🔑 Password for all demo users: {DEMO_PASSWORD}")
        print("================================\n")

    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
