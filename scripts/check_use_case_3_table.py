"""
Check Use Case 3 input_table_name
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT use_case_id, name, input_table_name 
        FROM use_cases 
        WHERE name = 'America Cash Equity Trading'
    """))
    row = result.fetchone()
    if row:
        print(f"Use Case ID: {row[0]}")
        print(f"Name: {row[1]}")
        print(f"input_table_name: {row[2]}")
    else:
        print("Use Case not found!")

