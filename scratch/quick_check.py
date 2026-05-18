from database import engine
from sqlalchemy import inspect
try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Connection SUCCESS! Tables: {tables}")
except Exception as e:
    print(f"Connection FAILED: {e}")
