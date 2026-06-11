import os
import sys
from sqlalchemy import create_engine, inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DATABASE_URL

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
columns = inspector.get_columns("alertness_readings")
print("Columns in alertness_readings:")
for col in columns:
    print(f"Name: {col['name']} | Type: {col['type']}")
