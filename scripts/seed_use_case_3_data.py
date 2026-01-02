"""
Phase 5.2: Seed Use Case 3 Fact Data
Generates 500 rows of mock data for fact_pnl_use_case_3 table.

CRITICAL: All amounts use Decimal type for precision.
Data is designed to "hit" the business rules:
- product_line='CORE Products' (Node 2)
- strategy='CORE' (multiple nodes)
- process_2='SWAP COMMISSION' (Node 6)
- Various dimensions to feed all rules
"""

import sys
import random
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.dependencies import get_session_factory


# Dimension values that "hit" the rules
PRODUCT_LINES = ["CORE Products", "NON-CORE Products", "Other Products"]
STRATEGIES = ["CORE", "ETF Amer", "NON-CORE", "Other Strategy"]
PROCESS_1_VALUES = ["MSET", "Other Process 1"]
PROCESS_2_VALUES = [
    "SWAP COMMISSION",
    "SD COMMISSION",
    "Inventory Management",
    "Other Process 2"
]
BOOK_VALUES = ["MSAL", "ETFUS", "Central Risk Book", "CRB Risk", "Other Book"]
COST_CENTERS = [f"CC_{i:03d}" for i in range(1, 21)]
DIVISIONS = ["Equity Trading", "Fixed Income", "Derivatives"]
BUSINESS_AREAS = ["Cash Equity", "Options", "Futures"]


def generate_mock_row(row_num: int, base_date: date) -> dict:
    """
    Generate a single mock row with data that hits the rules.
    
    Strategy:
    - 40% of rows have product_line='CORE Products' (hits Node 2)
    - 50% of rows have strategy='CORE' (hits multiple nodes)
    - 20% of rows have process_2='SWAP COMMISSION' (hits Node 6)
    - 15% of rows have process_2='SD COMMISSION' (hits Node 6)
    - 10% of rows have process_2='Inventory Management' (hits Node 9)
    - 20% of rows have book in ['MSAL', 'ETFUS', 'Central Risk Book', 'CRB Risk'] (hits Node 10)
    - 10% of rows have process_1='MSET' (hits Node 12)
    - 10% of rows have strategy='ETF Amer' (hits Node 11)
    """
    # Determine which rule to "hit" (weighted distribution)
    rule_target = random.choices(
        ["node2", "node10", "node6", "node9", "node11", "node12", "general"],
        weights=[40, 20, 20, 10, 10, 10, 10],
        k=1
    )[0]
    
    # Base values
    effective_date = base_date + timedelta(days=random.randint(0, 30))
    cost_center = random.choice(COST_CENTERS)
    division = random.choice(DIVISIONS)
    business_area = random.choice(BUSINESS_AREAS)
    
    # Rule-specific dimension values
    if rule_target == "node2":
        product_line = "CORE Products"
        strategy = random.choice(STRATEGIES)
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = random.choice(PROCESS_2_VALUES)
        book = random.choice(BOOK_VALUES)
    elif rule_target == "node10":
        product_line = random.choice(PRODUCT_LINES)
        strategy = "CORE"
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = random.choice(PROCESS_2_VALUES)
        book = random.choice(["MSAL", "ETFUS", "Central Risk Book", "CRB Risk"])
    elif rule_target == "node6":
        product_line = random.choice(PRODUCT_LINES)
        strategy = "CORE"
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = random.choice(["SWAP COMMISSION", "SD COMMISSION"])
        book = random.choice(BOOK_VALUES)
    elif rule_target == "node9":
        product_line = random.choice(PRODUCT_LINES)
        strategy = "CORE"
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = "Inventory Management"
        book = random.choice(BOOK_VALUES)
    elif rule_target == "node11":
        product_line = random.choice(PRODUCT_LINES)
        strategy = "ETF Amer"
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = random.choice(PROCESS_2_VALUES)
        book = random.choice(BOOK_VALUES)
    elif rule_target == "node12":
        product_line = random.choice(PRODUCT_LINES)
        strategy = random.choice(STRATEGIES)
        process_1 = "MSET"
        process_2 = random.choice(PROCESS_2_VALUES)
        book = random.choice(BOOK_VALUES)
    else:  # general
        product_line = random.choice(PRODUCT_LINES)
        strategy = random.choice(STRATEGIES)
        process_1 = random.choice(PROCESS_1_VALUES)
        process_2 = random.choice(PROCESS_2_VALUES)
        book = random.choice(BOOK_VALUES)
    
    # Generate amounts (using Decimal for precision)
    # Daily P&L: -100,000 to 100,000
    pnl_daily = Decimal(str(round(random.uniform(-100000, 100000), 2)))
    
    # Commission: 0 to 50,000 (only for CORE strategy)
    if strategy == "CORE":
        pnl_commission = Decimal(str(round(random.uniform(0, 50000), 2)))
    else:
        pnl_commission = Decimal('0')
    
    # Trade: 0 to 75,000 (only for CORE strategy with specific process_2)
    if strategy == "CORE" and process_2 in ["SWAP COMMISSION", "SD COMMISSION"]:
        pnl_trade = Decimal(str(round(random.uniform(0, 75000), 2)))
    else:
        pnl_trade = Decimal('0')
    
    return {
        "effective_date": effective_date,
        "cost_center": cost_center,
        "division": division,
        "business_area": business_area,
        "product_line": product_line,
        "strategy": strategy,
        "process_1": process_1,
        "process_2": process_2,
        "book": book,
        "pnl_daily": pnl_daily,
        "pnl_commission": pnl_commission,
        "pnl_trade": pnl_trade
    }


def insert_data_bulk(session: Session, rows: list):
    """Insert data using bulk insert for performance."""
    if not rows:
        return 0
    
    # Build INSERT statement
    sql = text("""
        INSERT INTO fact_pnl_use_case_3 (
            effective_date,
            cost_center,
            division,
            business_area,
            product_line,
            strategy,
            process_1,
            process_2,
            book,
            pnl_daily,
            pnl_commission,
            pnl_trade
        ) VALUES (
            :effective_date,
            :cost_center,
            :division,
            :business_area,
            :product_line,
            :strategy,
            :process_1,
            :process_2,
            :book,
            :pnl_daily,
            :pnl_commission,
            :pnl_trade
        )
    """)
    
    # Convert Decimal to string for SQL (PostgreSQL NUMERIC accepts string)
    data = []
    for row in rows:
        data.append({
            "effective_date": row["effective_date"],
            "cost_center": row["cost_center"],
            "division": row["division"],
            "business_area": row["business_area"],
            "product_line": row["product_line"],
            "strategy": row["strategy"],
            "process_1": row["process_1"],
            "process_2": row["process_2"],
            "book": row["book"],
            "pnl_daily": str(row["pnl_daily"]),  # Convert Decimal to string
            "pnl_commission": str(row["pnl_commission"]),
            "pnl_trade": str(row["pnl_trade"])
        })
    
    # Bulk insert
    session.execute(sql, data)
    session.commit()
    
    return len(data)


def verify_data(session: Session) -> dict:
    """Verify that data was inserted and check rule coverage."""
    # Count total rows
    count_sql = text("SELECT COUNT(*) FROM fact_pnl_use_case_3")
    total_count = session.execute(count_sql).scalar()
    
    # Check rule coverage
    coverage = {}
    
    # Node 2: product_line = 'CORE Products'
    sql = text("SELECT COUNT(*) FROM fact_pnl_use_case_3 WHERE product_line = 'CORE Products'")
    coverage["node2"] = session.execute(sql).scalar()
    
    # Node 10: strategy='CORE' AND book IN (...)
    sql = text("""
        SELECT COUNT(*) FROM fact_pnl_use_case_3 
        WHERE strategy = 'CORE' 
        AND book IN ('MSAL', 'ETFUS', 'Central Risk Book', 'CRB Risk')
    """)
    coverage["node10"] = session.execute(sql).scalar()
    
    # Node 6: strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')
    sql = text("""
        SELECT COUNT(*) FROM fact_pnl_use_case_3 
        WHERE strategy = 'CORE' 
        AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')
    """)
    coverage["node6"] = session.execute(sql).scalar()
    
    # Node 9: strategy='CORE' AND process_2='Inventory Management'
    sql = text("""
        SELECT COUNT(*) FROM fact_pnl_use_case_3 
        WHERE strategy = 'CORE' 
        AND process_2 = 'Inventory Management'
    """)
    coverage["node9"] = session.execute(sql).scalar()
    
    # Node 11: strategy='ETF Amer'
    sql = text("SELECT COUNT(*) FROM fact_pnl_use_case_3 WHERE strategy = 'ETF Amer'")
    coverage["node11"] = session.execute(sql).scalar()
    
    # Node 12: process_1='MSET'
    sql = text("SELECT COUNT(*) FROM fact_pnl_use_case_3 WHERE process_1 = 'MSET'")
    coverage["node12"] = session.execute(sql).scalar()
    
    return {
        "total": total_count,
        "coverage": coverage
    }


def main():
    """Main execution function."""
    print("="*70)
    print("Phase 5.2: Seed Use Case 3 Fact Data")
    print("="*70)
    print("Generating 500 rows of mock data...")
    print("CRITICAL: All amounts use Decimal type for precision")
    print()
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        # Check if data already exists
        check_sql = text("SELECT COUNT(*) FROM fact_pnl_use_case_3")
        existing_count = session.execute(check_sql).scalar()
        
        if existing_count > 0:
            print(f"[WARN] Table already contains {existing_count} rows")
            response = input("Do you want to delete existing data and regenerate? (yes/no): ")
            if response.lower() == "yes":
                delete_sql = text("DELETE FROM fact_pnl_use_case_3")
                session.execute(delete_sql)
                session.commit()
                print("[OK] Deleted existing data")
            else:
                print("[SKIP] Keeping existing data")
                return 0
        
        # Generate data
        base_date = date(2024, 1, 1)
        rows = []
        
        print("Generating rows...")
        for i in range(500):
            row = generate_mock_row(i, base_date)
            rows.append(row)
            
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/500 rows...")
        
        # Insert data (in batches of 100 for performance)
        print("\nInserting data into database...")
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            inserted = insert_data_bulk(session, batch)
            total_inserted += inserted
            print(f"  Inserted batch {i//batch_size + 1}: {inserted} rows")
        
        # Verify data
        print("\nVerifying data...")
        stats = verify_data(session)
        
        print("\n" + "="*70)
        print("[SUCCESS] Use Case 3 fact data created successfully!")
        print("="*70)
        print(f"Total rows: {stats['total']}")
        print("\nRule coverage:")
        print(f"  Node 2 (CORE Products): {stats['coverage']['node2']} rows")
        print(f"  Node 10 (CRB): {stats['coverage']['node10']} rows")
        print(f"  Node 6 (Swap Commission): {stats['coverage']['node6']} rows")
        print(f"  Node 9 (Inventory Management): {stats['coverage']['node9']} rows")
        print(f"  Node 11 (ETF Amber): {stats['coverage']['node11']} rows")
        print(f"  Node 12 (MSET): {stats['coverage']['node12']} rows")
        
        return 0
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Failed to create data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

