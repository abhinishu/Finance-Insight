"""
Mock Trading Data Generator for Phase 5 (Rich Trading Use Case)
Generates 500 rows of realistic trading P&L data for fact_trading_pnl table.
"""

import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import FactTradingPnl, UseCase, UseCaseStatus


def get_last_n_business_days(n: int = 5) -> list[date]:
    """
    Get the last N business days (excluding weekends).
    
    Args:
        n: Number of business days to return
    
    Returns:
        List of date objects (most recent first)
    """
    business_days = []
    current_date = date.today()
    
    while len(business_days) < n:
        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:  # Monday to Friday
            business_days.append(current_date)
        current_date -= timedelta(days=1)
    
    return business_days


def generate_trading_data(
    use_case_id: Optional[UUID] = None,
    num_rows: int = 500
) -> dict:
    """
    Generate and insert trading P&L data into fact_trading_pnl table.
    
    Args:
        use_case_id: UUID of the use case. If None, uses first active use case.
        num_rows: Number of rows to generate (default: 500)
    
    Returns:
        Dictionary with generation statistics
    """
    session: Session = SessionLocal()
    should_close = True
    
    try:
        # Get or find use case
        if use_case_id is None:
            use_case = session.query(UseCase).filter(
                UseCase.status == UseCaseStatus.ACTIVE
            ).first()
            
            if use_case is None:
                raise ValueError(
                    "No active use case found. Please create a use case first or provide a use_case_id."
                )
            use_case_id = use_case.use_case_id
            print(f"Using use case: {use_case.name} ({use_case_id})")
        else:
            use_case = session.query(UseCase).filter(
                UseCase.use_case_id == use_case_id
            ).first()
            
            if use_case is None:
                raise ValueError(f"Use case '{use_case_id}' not found")
            print(f"Using use case: {use_case.name} ({use_case_id})")
        
        # Get last 5 business days
        business_dates = get_last_n_business_days(5)
        print(f"Generating data for dates: {[d.strftime('%Y-%m-%d') for d in business_dates]}")
        
        # Dimension values
        divisions = ['IED', 'FID', 'IBD']
        business_areas = ['Cash Equity', 'Derivatives', 'Prime Brokerage', 'Credit']
        product_lines = ['Core Products', 'Structured Products', 'Flow Products', 'Exotic Products']
        strategies = ['CORE', 'VOL', 'ARB', 'INDEX']
        books = ['CORE 1', 'CORE 2', 'VOL 1', 'ARB 1', 'INDEX 1']
        company_codes = ['1234', '5678', '9012']
        cost_centers = ['ABC1', 'DEF2', 'GHI3', 'JKL4', 'MNO5']
        taps_accounts = [f'TAPS_{i:03d}' for i in range(1, 21)]  # TAPS_001 to TAPS_020
        
        # Generate rows
        generated = 0
        for i in range(num_rows):
            # Random date from business days
            effective_date = random.choice(business_dates)
            
            # Random dimensions
            division = random.choice(divisions)
            business_area = random.choice(business_areas)
            product_line = random.choice(product_lines)
            strategy = random.choice(strategies)
            book = random.choice(books)
            company_code = random.choice(company_codes)
            cost_center = random.choice(cost_centers)
            taps_account = random.choice(taps_accounts)
            
            # Generate P&L values (random between -1000 and +1000)
            daily_pnl = Decimal(str(random.uniform(-1000, 1000))).quantize(Decimal('0.01'))
            wtd_pnl = Decimal(str(random.uniform(-5000, 5000))).quantize(Decimal('0.01'))
            mtd_pnl = Decimal(str(random.uniform(-20000, 20000))).quantize(Decimal('0.01'))
            qtd_pnl = Decimal(str(random.uniform(-60000, 60000))).quantize(Decimal('0.01'))
            ytd_pnl = Decimal(str(random.uniform(-200000, 200000))).quantize(Decimal('0.01'))
            
            # Create entry
            entry = FactTradingPnl(
                use_case_id=use_case_id,
                effective_date=effective_date,
                taps_account=taps_account,
                company_code=company_code,
                cost_center=cost_center,
                division=division,
                business_area=business_area,
                product_line=product_line,
                strategy=strategy,
                book=book,
                daily_pnl=daily_pnl,
                wtd_pnl=wtd_pnl,
                mtd_pnl=mtd_pnl,
                qtd_pnl=qtd_pnl,
                ytd_pnl=ytd_pnl
            )
            
            session.add(entry)
            generated += 1
            
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1}/{num_rows} rows...")
        
        # Commit transaction
        session.commit()
        
        # Verify count
        final_count = session.query(FactTradingPnl).filter(
            FactTradingPnl.use_case_id == use_case_id
        ).count()
        
        result = {
            "generated": generated,
            "final_row_count": final_count,
            "use_case_id": str(use_case_id),
            "use_case_name": use_case.name,
            "dates_used": [d.strftime('%Y-%m-%d') for d in business_dates]
        }
        
        print(f"\n✅ Successfully generated {generated} rows")
        print(f"   Final count in database: {final_count}")
        print(f"   Use case: {use_case.name}")
        
        return result
    
    except Exception as e:
        session.rollback()
        print(f"❌ Error generating trading data: {e}")
        raise
    
    finally:
        if should_close:
            session.close()


def main():
    """CLI interface for trading data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate mock trading P&L data for fact_trading_pnl table"
    )
    parser.add_argument(
        "--use-case-id",
        type=str,
        help="UUID of the use case (if not provided, uses first active use case)"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=500,
        help="Number of rows to generate (default: 500)"
    )
    
    args = parser.parse_args()
    
    use_case_id = None
    if args.use_case_id:
        try:
            use_case_id = UUID(args.use_case_id)
        except ValueError:
            print(f"❌ Invalid UUID format: {args.use_case_id}")
            return 1
    
    try:
        result = generate_trading_data(use_case_id=use_case_id, num_rows=args.rows)
        return 0
    except Exception as e:
        print(f"❌ Failed to generate trading data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())



