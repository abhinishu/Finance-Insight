"""Quick verification script for Use Case 3 seed data."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    nodes = conn.execute(text(
        "SELECT count(*) FROM dim_hierarchy WHERE atlas_source = 'America Cash Equity Trading Structure'"
    )).scalar()
    
    type3 = conn.execute(text(
        "SELECT count(*) FROM metadata_rules WHERE rule_type = 'NODE_ARITHMETIC'"
    )).scalar()
    
    data = conn.execute(text(
        "SELECT count(*) FROM fact_pnl_use_case_3"
    )).scalar()
    
    print(f"Nodes: {nodes}")
    print(f"Type 3 Rules: {type3}")
    print(f"Data Rows: {data}")

