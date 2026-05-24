import os
import sys
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
from routers.risk_prediction import get_fleet_predictions

class DummyUser:
    id = 1
    role = "safety_officer"

db = SessionLocal()
try:
    res = get_fleet_predictions(db, DummyUser())
    print("KPIs:", res["kpi"])
    print("Rankings count:", len(res["rankings"]))
    for r in res["rankings"]:
        print(f"Rank {r['rank']} | ID {r['id']} | Name: {r['name']} | Score: {r['score']} | Level: {r['level']} | Status: {r['status']}")
finally:
    db.close()
