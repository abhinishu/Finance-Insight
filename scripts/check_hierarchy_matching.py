"""
Check hierarchy node_ids vs fact_pnl_entries category_codes
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def check_matching():
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("HIERARCHY vs FACT_PNL_ENTRIES MATCHING CHECK")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Check Project Sterling
        print("\n--- PROJECT STERLING ---")
        sterling_id = 'a26121d8-9e01-4e70-9761-588b1854fe06'
        
        # Get category_codes from fact_pnl_entries
        cat_codes = conn.execute(text("""
            SELECT DISTINCT category_code 
            FROM fact_pnl_entries 
            WHERE use_case_id = :id
            ORDER BY category_code
            LIMIT 10
        """), {"id": sterling_id}).fetchall()
        print(f"Category codes in fact_pnl_entries: {[r[0] for r in cat_codes]}")
        
        # Get node_ids from hierarchy
        node_ids = conn.execute(text("""
            SELECT DISTINCT node_id 
            FROM dim_hierarchy 
            WHERE atlas_source LIKE '%Sterling%' OR atlas_source LIKE '%Mock%'
            ORDER BY node_id
            LIMIT 20
        """)).fetchall()
        print(f"Node IDs in hierarchy: {[r[0] for r in node_ids]}")
        
        # Check for matches
        cat_code_set = {r[0] for r in cat_codes}
        node_id_set = {r[0] for r in node_ids}
        matches = cat_code_set.intersection(node_id_set)
        print(f"\nMatches: {matches}")
        print(f"Match count: {len(matches)}")
        
        # Check America Trading
        print("\n--- AMERICA TRADING ---")
        america_id = 'b90f1708-4087-4117-9820-9226ed1115bb'
        
        cat_codes2 = conn.execute(text("""
            SELECT DISTINCT category_code 
            FROM fact_pnl_entries 
            WHERE use_case_id = :id
            ORDER BY category_code
            LIMIT 10
        """), {"id": america_id}).fetchall()
        print(f"Category codes in fact_pnl_entries: {[r[0] for r in cat_codes2]}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_matching()

