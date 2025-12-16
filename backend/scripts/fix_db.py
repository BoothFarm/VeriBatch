from sqlalchemy import text
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.db.database import engine

def fix_schema():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE batches ADD COLUMN is_mock_recall BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("Successfully added is_mock_recall column.")
        except Exception as e:
            print(f"Error (maybe column exists?): {e}")

if __name__ == "__main__":
    fix_schema()
