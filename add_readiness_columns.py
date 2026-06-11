import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:impano12@127.0.0.1:5432/aeroguard_db"
)

def run_migration():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    columns_to_add = [
        ("apple_watch_sleep_hours", "DOUBLE PRECISION"),
        ("apple_watch_sleep_quality", "DOUBLE PRECISION"),
        ("apple_watch_resting_hr", "DOUBLE PRECISION"),
        ("apple_watch_current_hr", "DOUBLE PRECISION"),
        ("apple_watch_activity_level", "DOUBLE PRECISION"),
        ("self_alertness_level", "DOUBLE PRECISION"),
        ("alcohol_declared", "BOOLEAN DEFAULT FALSE"),
        ("reaction_time_ms", "DOUBLE PRECISION")
    ]
    
    with engine.begin() as conn:
        for col_name, col_type in columns_to_add:
            try:
                # PostgreSQL check if column exists
                query = text(f"""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 
                            FROM information_schema.columns 
                            WHERE table_name='fitness_assessments' AND column_name='{col_name}'
                        ) THEN 
                            ALTER TABLE fitness_assessments ADD COLUMN {col_name} {col_type};
                        END IF; 
                    END $$;
                """)
                conn.execute(query)
                print(f"Column '{col_name}' checked/added successfully.")
            except Exception as e:
                print(f"Error checking/adding column '{col_name}': {e}")

if __name__ == "__main__":
    run_migration()
