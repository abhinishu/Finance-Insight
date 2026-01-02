"""
Fix Use Case 3 input_table_name
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
        UPDATE use_cases 
        SET input_table_name = 'fact_pnl_use_case_3' 
        WHERE name = 'America Cash Equity Trading'
    """))
    conn.commit()
    print(f"Updated {result.rowcount} row(s)")
    print("Use Case 3 now has input_table_name = 'fact_pnl_use_case_3'")

