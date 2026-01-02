"""
Comprehensive Data Population Script - Fill All Zero Nodes
Ensures every hierarchy node has non-zero values for Daily, MTD, and YTD P&L.

This script:
1. For Use Case 1 (America Trading P&L): Populates fact_pnl_gold for all hierarchy nodes
2. For Use Case 3 (America Cash Equity Trading): Populates fact_pnl_use_case_3 for all hierarchy nodes
3. Ensures MTD/YTD are populated using formulas
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models import FactPnlGold, FactPnlUseCase3, DimHierarchy, UseCase
from uuid import uuid4

def populate_use_case_1(db: Session):
    """
    Populate all zero nodes for Use Case 1 (America Trading P&L).
    """
    print("=" * 80)
    print("USE CASE 1: America Trading P&L - Populate All Zero Nodes")
    print("=" * 80)
    print()
    
    # Find Use Case 1
    use_case_1 = db.query(UseCase).filter(
        UseCase.name.ilike('%America Trading%')
    ).first()
    
    if not use_case_1:
        print("  [ERROR] Use Case 1 (America Trading P&L) not found!")
        return
    
    print(f"  Use Case: {use_case_1.name}")
    print(f"  Use Case ID: {use_case_1.use_case_id}")
    print()
    
    # Get all leaf nodes from hierarchy
    atlas_source = use_case_1.atlas_structure_id
    leaf_nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_source,
        DimHierarchy.is_leaf == True
    ).all()
    
    print(f"  Found {len(leaf_nodes)} leaf nodes in hierarchy")
    print()
    
    # Check current data and populate missing nodes
    inserted_count = 0
    updated_count = 0
    
    for node in leaf_nodes:
        node_id = node.node_id
        node_name = node.node_name
        
        # Check current sum for this CC ID
        current_sum = db.query(func.sum(FactPnlGold.daily_pnl)).filter(
            FactPnlGold.cc_id == node_id
        ).scalar()
        current_sum = Decimal(str(current_sum or 0))
        
        # Determine target daily_pnl based on node name
        target_daily = Decimal('20000')  # Default
        if 'PROG_TRADING' in node_id:
            target_daily = Decimal('15000')
        elif 'INDEX_ARB' in node_id:
            target_daily = Decimal('22000')
        elif 'ALGO' in node_id:
            target_daily = Decimal('35000')
        elif 'CASH_NY' in node_id:
            target_daily = Decimal('25000')
        
        if current_sum == Decimal('0') or current_sum < target_daily:
            # Calculate how much to add
            if current_sum == Decimal('0'):
                daily_pnl = target_daily
            else:
                daily_pnl = target_daily - current_sum
            
            mtd_pnl = daily_pnl * Decimal('5')
            ytd_pnl = daily_pnl * Decimal('20')
            
            # Insert new row
            new_fact = FactPnlGold(
                fact_id=uuid4(),
                account_id=f"ACC_{node_id}",
                cc_id=node_id,
                book_id=f"BOOK_{node_id[-3:] if len(node_id) >= 3 else '001'}",
                strategy_id=f"STRAT_{node_id[-3:] if len(node_id) >= 3 else '001'}",
                trade_date=date.today(),
                daily_pnl=daily_pnl,
                mtd_pnl=mtd_pnl,
                ytd_pnl=ytd_pnl,
                pytd_pnl=Decimal('0')
            )
            
            db.add(new_fact)
            inserted_count += 1
            if current_sum == Decimal('0'):
                print(f"  [INSERT] '{node_id}' ({node_name}): daily={daily_pnl}, mtd={mtd_pnl}, ytd={ytd_pnl}")
            else:
                print(f"  [ADD] '{node_id}' ({node_name}): Added daily={daily_pnl} (existing: {current_sum}, target: {target_daily})")
        else:
            # Check if MTD/YTD are zero
            mtd_sum = db.query(func.sum(FactPnlGold.mtd_pnl)).filter(
                FactPnlGold.cc_id == node_id
            ).scalar()
            mtd_sum = Decimal(str(mtd_sum or 0))
            
            ytd_sum = db.query(func.sum(FactPnlGold.ytd_pnl)).filter(
                FactPnlGold.cc_id == node_id
            ).scalar()
            ytd_sum = Decimal(str(ytd_sum or 0))
            
            if mtd_sum == Decimal('0') or ytd_sum == Decimal('0'):
                # Update existing rows to populate MTD/YTD
                update_count = db.query(FactPnlGold).filter(
                    FactPnlGold.cc_id == node_id
                ).update({
                    FactPnlGold.mtd_pnl: FactPnlGold.daily_pnl * 5,
                    FactPnlGold.ytd_pnl: FactPnlGold.daily_pnl * 20
                })
                updated_count += update_count
                print(f"  [UPDATE] '{node_id}' ({node_name}): Updated {update_count} rows with MTD/YTD formulas")
    
    db.commit()
    print()
    print(f"  Summary: {inserted_count} rows inserted, {updated_count} rows updated")
    print()
    
    # Verification
    print("  Verification:")
    for node in leaf_nodes:
        daily_sum = db.query(func.sum(FactPnlGold.daily_pnl)).filter(
            FactPnlGold.cc_id == node.node_id
        ).scalar()
        mtd_sum = db.query(func.sum(FactPnlGold.mtd_pnl)).filter(
            FactPnlGold.cc_id == node.node_id
        ).scalar()
        ytd_sum = db.query(func.sum(FactPnlGold.ytd_pnl)).filter(
            FactPnlGold.cc_id == node.node_id
        ).scalar()
        
        daily_sum = Decimal(str(daily_sum or 0))
        mtd_sum = Decimal(str(mtd_sum or 0))
        ytd_sum = Decimal(str(ytd_sum or 0))
        
        if daily_sum != Decimal('0') and mtd_sum != Decimal('0') and ytd_sum != Decimal('0'):
            print(f"    [PASS] '{node.node_id}': Daily={daily_sum}, MTD={mtd_sum}, YTD={ytd_sum}")
        else:
            print(f"    [FAIL] '{node.node_id}': Daily={daily_sum}, MTD={mtd_sum}, YTD={ytd_sum}")
    print()


def populate_use_case_3(db: Session):
    """
    Populate all zero nodes for Use Case 3 (America Cash Equity Trading).
    """
    print("=" * 80)
    print("USE CASE 3: America Cash Equity Trading - Populate All Zero Nodes")
    print("=" * 80)
    print()
    
    # Find Use Case 3
    use_case_3 = db.query(UseCase).filter(
        UseCase.name.ilike('%Cash Equity%')
    ).first()
    
    if not use_case_3:
        print("  [ERROR] Use Case 3 (America Cash Equity Trading) not found!")
        return
    
    print(f"  Use Case: {use_case_3.name}")
    print(f"  Use Case ID: {use_case_3.use_case_id}")
    print()
    
    # Get all nodes from hierarchy (not just leaves, as we match by strategy/product_line)
    atlas_source = use_case_3.atlas_structure_id
    all_nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_source
    ).all()
    
    print(f"  Found {len(all_nodes)} nodes in hierarchy")
    print()
    
    # Get current data distribution
    from app.engine.waterfall import load_facts_from_use_case_3
    import pandas as pd
    
    try:
        facts_df = load_facts_from_use_case_3(db, use_case_id=use_case_3.use_case_id)
    except Exception as e:
        print(f"  [ERROR] Failed to load facts: {e}")
        facts_df = pd.DataFrame()
    
    if facts_df.empty:
        print("  [WARNING] No facts found, creating initial data...")
        facts_df = pd.DataFrame()
    
    # Map of node_name -> minimum required daily_pnl to ensure non-zero
    # This ensures every node has at least some data
    node_requirements = {
        'CORE Products': Decimal('100000'),  # Parent - will aggregate from children
        'Core Ex CRB': Decimal('50000'),
        'Commissions': Decimal('30000'),
        'Commissions (Non Swap)': Decimal('20000'),
        'Swap Commission': Decimal('10000'),
        'Trading': Decimal('20000'),
        'Facilitations': Decimal('10000'),
        'Inventory Management': Decimal('10000'),
        'CRB': Decimal('15000'),
        'ETF Amber': Decimal('25000'),
        'MSET': Decimal('35000'),
    }
    
    inserted_count = 0
    
    for node in all_nodes:
        node_name = node.node_name
        
        if not node_name:
            continue
        
        # Skip ROOT node - it will aggregate from children
        if node.parent_node_id is None:
            continue
        
        # Check if this node has matching data with non-zero sum
        has_data = False
        daily_sum = Decimal('0')
        mtd_sum = Decimal('0')
        ytd_sum = Decimal('0')
        
        if not facts_df.empty:
            if 'strategy' in facts_df.columns:
                strategy_match = facts_df[facts_df['strategy'].str.upper() == node_name.upper()]
                if len(strategy_match) > 0:
                    daily_sum = Decimal(str(strategy_match['pnl_daily'].sum()))
                    mtd_sum = Decimal(str(strategy_match['pnl_commission'].sum()))
                    ytd_sum = Decimal(str(strategy_match['pnl_trade'].sum()))
                    if daily_sum != Decimal('0'):
                        has_data = True
            
            if not has_data and 'product_line' in facts_df.columns:
                product_match = facts_df[facts_df['product_line'].str.upper() == node_name.upper()]
                if len(product_match) > 0:
                    daily_sum = Decimal(str(product_match['pnl_daily'].sum()))
                    mtd_sum = Decimal(str(product_match['pnl_commission'].sum()))
                    ytd_sum = Decimal(str(product_match['pnl_trade'].sum()))
                    if daily_sum != Decimal('0'):
                        has_data = True
        
        # Check if we need to add more data
        required_daily = node_requirements.get(node_name, Decimal('15000'))
        
        if not has_data or daily_sum < required_daily:
            # Calculate how much to add
            if has_data:
                add_daily = required_daily - daily_sum
            else:
                add_daily = required_daily
            
            # Generate additional data
            mtd_pnl = add_daily * Decimal('2.5')
            ytd_pnl = add_daily * Decimal('10.0')
            
            # Determine strategy based on node name
            strategy = node_name
            
            # Insert new row(s) to reach required amount
            # Insert multiple rows to make it more realistic
            rows_to_insert = max(1, int(add_daily / Decimal('10000')))  # 1 row per 10k
            daily_per_row = add_daily / Decimal(str(rows_to_insert))
            mtd_per_row = daily_per_row * Decimal('2.5')
            ytd_per_row = daily_per_row * Decimal('10.0')
            
            for i in range(rows_to_insert):
                new_fact = FactPnlUseCase3(
                    entry_id=uuid4(),
                    effective_date=date.today(),
                    cost_center=f"CC_{node_name[:10].replace(' ', '_')}_{i}",
                    division="Trading",
                    business_area="Cash Equity",
                    product_line=node_name if 'Product' in node_name or 'CRB' in node_name else None,
                    strategy=strategy,
                    process_1="Trading Process",
                    process_2="TRADING" if 'Trading' in node_name else ("COMMISSION" if 'Commission' in node_name else "OTHER"),
                    book=f"BOOK_{node_name[:5].replace(' ', '_')}",
                    pnl_daily=daily_per_row,
                    pnl_commission=mtd_per_row,
                    pnl_trade=ytd_per_row
                )
                
                db.add(new_fact)
                inserted_count += 1
            
            if has_data:
                print(f"  [ADD] '{node_name}': Added {rows_to_insert} rows, daily={add_daily} (existing: {daily_sum}, target: {required_daily})")
            else:
                print(f"  [INSERT] '{node_name}': Inserted {rows_to_insert} rows, daily={add_daily}, mtd={mtd_pnl}, ytd={ytd_pnl}")
    
    db.commit()
    print()
    print(f"  Summary: {inserted_count} rows inserted")
    print()
    
    # Verification - reload facts and check all nodes
    try:
        facts_df_updated = load_facts_from_use_case_3(db, use_case_id=use_case_3.use_case_id)
        
        print("  Verification (all nodes):")
        for node in all_nodes:
            if node.node_name and node.parent_node_id is not None:
                node_name = node.node_name
                
                # Check if data exists
                if not facts_df_updated.empty:
                    if 'strategy' in facts_df_updated.columns:
                        match = facts_df_updated[facts_df_updated['strategy'].str.upper() == node_name.upper()]
                        if len(match) > 0:
                            daily_sum = Decimal(str(match['pnl_daily'].sum()))
                            mtd_sum = Decimal(str(match['pnl_commission'].sum()))
                            ytd_sum = Decimal(str(match['pnl_trade'].sum()))
                            
                            if daily_sum != Decimal('0') and mtd_sum != Decimal('0') and ytd_sum != Decimal('0'):
                                print(f"    [PASS] '{node_name}': Daily={daily_sum}, MTD={mtd_sum}, YTD={ytd_sum}")
                            else:
                                print(f"    [PARTIAL] '{node_name}': Daily={daily_sum}, MTD={mtd_sum}, YTD={ytd_sum}")
                        else:
                            print(f"    [FAIL] '{node_name}': No matching data found")
    except Exception as e:
        print(f"  [WARNING] Verification failed: {e}")
    print()


def populate_all_zero_nodes():
    """
    Main function to populate all zero nodes for both use cases.
    """
    print("=" * 80)
    print("COMPREHENSIVE DATA POPULATION - Fill All Zero Nodes")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Populate Use Case 1
        populate_use_case_1(db)
        
        # Populate Use Case 3
        populate_use_case_3(db)
        
        print("=" * 80)
        print("POPULATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_all_zero_nodes()

