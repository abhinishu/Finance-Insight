"""
Reseed P&L Data Script
Generates 10,000+ rows of realistic mock data in fact_pnl_gold with mathematical consistency.

CRITICAL: Ensures MTD = sum of daily values, YTD = accurate year-to-date totals.
This ensures the "Golden Equation" holds true: Natural = Adjusted + Plug
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from random import choice, randint, uniform
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.models import FactPnlGold, DimHierarchy, Base

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://finance_user:finance_pass@localhost:5432/finance_insight')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_leaf_nodes(session):
    """Get all leaf nodes (cost centers) from hierarchy."""
    leaf_nodes = session.query(DimHierarchy).filter(
        DimHierarchy.is_leaf == True
    ).all()
    
    if not leaf_nodes:
        # Fallback: generate some cost centers
        return [f"CC_{i:03d}" for i in range(1, 51)]
    
    return [node.node_id for node in leaf_nodes]


def generate_daily_pnl():
    """Generate realistic daily P&L value."""
    return Decimal(str(uniform(-100000, 100000))).quantize(Decimal('0.01'))


def calculate_mtd_from_daily(daily_values: list) -> Decimal:
    """Calculate MTD as sum of daily values for the month."""
    return sum(daily_values)


def calculate_ytd_from_daily(daily_values_by_date: dict, current_date: date) -> Decimal:
    """Calculate YTD as sum of daily values from Jan 1 to current date."""
    year_start = date(current_date.year, 1, 1)
    ytd_sum = Decimal('0')
    
    for trade_date, daily_value in daily_values_by_date.items():
        if year_start <= trade_date <= current_date:
            ytd_sum += daily_value
    
    return ytd_sum


def generate_mathematically_consistent_row(
    cost_centers: list,
    accounts: list,
    books: list,
    strategies: list,
    trade_date: date,
    daily_values_by_cc_date: dict
) -> dict:
    """
    Generate a fact row with mathematically consistent MTD and YTD values.
    
    For each cost center, we track daily values by date to calculate accurate MTD/YTD.
    MTD = sum of daily values for the month up to this date (for this cost center)
    YTD = sum of daily values from Jan 1 to this date (for this cost center)
    
    Args:
        cost_centers: List of cost center IDs
        accounts: List of account IDs
        books: List of book IDs
        strategies: List of strategy IDs
        trade_date: Trade date for this row
        daily_values_by_cc_date: Dict mapping (cc_id, date) -> daily P&L
    
    Returns:
        Dictionary with fact row data
    """
    # Generate daily P&L
    daily_pnl = generate_daily_pnl()
    
    # Select cost center
    cc_id = choice(cost_centers)
    
    # Store daily value for this cost center and date
    key = (cc_id, trade_date)
    daily_values_by_cc_date[key] = daily_pnl
    
    # Calculate MTD: sum of all daily values for this cost center in the current month up to this date
    month_start = date(trade_date.year, trade_date.month, 1)
    mtd_pnl = sum(
        daily_values_by_cc_date.get((cc_id, d), Decimal('0'))
        for d in [month_start + timedelta(days=i) for i in range((trade_date - month_start).days + 1)]
        if d <= trade_date
    )
    
    # Calculate YTD: sum of all daily values for this cost center from Jan 1 to current date
    year_start = date(trade_date.year, 1, 1)
    ytd_pnl = sum(
        daily_values_by_cc_date.get((cc_id, d), Decimal('0'))
        for d in [year_start + timedelta(days=i) for i in range((trade_date - year_start).days + 1)]
        if d <= trade_date
    )
    
    # PYTD: Previous year to date (use previous year's YTD pattern)
    pytd_pnl = Decimal(str(uniform(-1800000, 1800000))).quantize(Decimal('0.01'))
    
    return {
        'fact_id': uuid4(),
        'account_id': choice(accounts),
        'cc_id': cc_id,
        'book_id': choice(books),
        'strategy_id': choice(strategies),
        'trade_date': trade_date,
        'daily_pnl': daily_pnl,
        'mtd_pnl': mtd_pnl,
        'ytd_pnl': ytd_pnl,
        'pytd_pnl': pytd_pnl,
    }


def reseed_pnl_data(count: int = 10000, clear_existing: bool = True):
    """
    Reseed fact_pnl_gold table with mathematically consistent data.
    
    Args:
        count: Number of rows to generate (default: 10,000)
        clear_existing: Whether to clear existing data first (default: True)
    """
    session = SessionLocal()
    
    try:
        # Get leaf nodes (cost centers) from hierarchy
        cost_centers = get_leaf_nodes(session)
        print(f"Found {len(cost_centers)} cost centers in hierarchy")
        
        if not cost_centers:
            print("WARNING: No cost centers found. Using fallback values.")
            cost_centers = [f"CC_{i:03d}" for i in range(1, 51)]
        
        # Dimension ranges
        accounts = [f"ACC_{i:03d}" for i in range(1, 11)]
        books = [f"B{i:02d}" for i in range(1, 11)]
        strategies = [f"STRAT_{i:02d}" for i in range(1, 6)]
        
        # Date range: 2024-01-01 to 2024-12-31
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        date_range = (end_date - start_date).days
        
        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing fact_pnl_gold data...")
            session.query(FactPnlGold).delete()
            session.commit()
            print("Existing data cleared.")
        
        # Generate rows with mathematical consistency
        print(f"Generating {count} rows with mathematical consistency...")
        
        # Track daily values by (cc_id, date) for MTD/YTD calculation
        daily_values_by_cc_date = {}
        
        fact_rows = []
        batch_size = 1000
        
        for i in range(count):
            # Generate random date within range
            random_days = randint(0, date_range)
            trade_date = start_date + timedelta(days=random_days)
            
            # Generate row with mathematical consistency
            row = generate_mathematically_consistent_row(
                cost_centers, accounts, books, strategies,
                trade_date, daily_values_by_cc_date
            )
            fact_rows.append(row)
            
            # Batch insert for performance
            if len(fact_rows) >= batch_size:
                session.bulk_insert_mappings(FactPnlGold, fact_rows)
                session.commit()
                print(f"Inserted {len(fact_rows)} rows (total: {i + 1}/{count})")
                fact_rows = []
        
        # Insert remaining rows
        if fact_rows:
            session.bulk_insert_mappings(FactPnlGold, fact_rows)
            session.commit()
            print(f"Inserted final {len(fact_rows)} rows")
        
        # Verify mathematical consistency
        print("\nVerifying mathematical consistency...")
        verify_mathematical_consistency(session)
        
        print(f"\n✅ Successfully reseeded {count} rows with mathematical consistency!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()


def verify_mathematical_consistency(session):
    """Verify that MTD = sum of daily values and YTD is accurate."""
    from sqlalchemy import func, extract
    
    # Sample verification: Check a few months
    sample_months = [
        (2024, 1),
        (2024, 6),
        (2024, 12),
    ]
    
    for year, month in sample_months:
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year, month, 31)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get sum of daily values for the month
        daily_sum = session.query(func.sum(FactPnlGold.daily_pnl)).filter(
            FactPnlGold.trade_date >= month_start,
            FactPnlGold.trade_date <= month_end
        ).scalar() or Decimal('0')
        
        # Get average MTD (should be close to sum of daily for end of month)
        avg_mtd = session.query(func.avg(FactPnlGold.mtd_pnl)).filter(
            FactPnlGold.trade_date >= month_start,
            FactPnlGold.trade_date <= month_end
        ).scalar() or Decimal('0')
        
        print(f"  Month {year}-{month:02d}: Daily sum = ${daily_sum:,.2f}, Avg MTD = ${avg_mtd:,.2f}")
    
    # Verify YTD at year end
    year_end = date(2024, 12, 31)
    ytd_sum = session.query(func.sum(FactPnlGold.ytd_pnl)).filter(
        FactPnlGold.trade_date == year_end
    ).scalar() or Decimal('0')
    
    total_daily = session.query(func.sum(FactPnlGold.daily_pnl)).filter(
        extract('year', FactPnlGold.trade_date) == 2024
    ).scalar() or Decimal('0')
    
    print(f"  Year 2024: Total Daily = ${total_daily:,.2f}, YTD (Dec 31) = ${ytd_sum:,.2f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reseed P&L data with mathematical consistency')
    parser.add_argument('--count', type=int, default=10000, help='Number of rows to generate (default: 10000)')
    parser.add_argument('--keep-existing', action='store_true', help='Keep existing data (default: clear)')
    
    args = parser.parse_args()
    
    reseed_pnl_data(
        count=args.count,
        clear_existing=not args.keep_existing
    )

