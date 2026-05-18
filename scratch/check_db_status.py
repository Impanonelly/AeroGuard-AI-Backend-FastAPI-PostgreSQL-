from database import engine
from sqlalchemy import inspect
import sys

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Connection Successful!")
    print(f"Tables found: {tables}")
except Exception as e:
    print(f"Connection Failed: {e}")
    sys.exit(1)
