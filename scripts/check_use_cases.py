"""
Check all use cases and their input_table_name values
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT name, input_table_name FROM use_cases"))
    rows = result.fetchall()
    
    print("Use Cases:")
    print("-" * 70)
    print(f"{'Name':<40} | {'input_table_name':<30}")
    print("-" * 70)
    
    for row in rows:
        name = row[0] or "NULL"
        input_table_name = row[1] or "NULL"
        print(f"{name:<40} | {input_table_name:<30}")


