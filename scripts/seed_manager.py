"""
Seed Manager for Finance-Insight
Reads pilot_seed.json and inserts data into the database using upsert logic.
PRO Requirement: Uses "ON CONFLICT DO NOTHING" to prevent duplicates.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal
from typing import Dict, List, Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import create_db_engine, get_database_url, get_session_factory
from app.models import FactPnlGold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_seed_data(seed_file: Path) -> Dict[str, Any]:
    """
    Load seed data from JSON file.
    
    Args:
        seed_file: Path to pilot_seed.json
        
    Returns:
        Dictionary with 'categories' and 'pilot_rows' keys
    """
    try:
        with open(seed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded seed data from {seed_file}")
        return data
    except FileNotFoundError:
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in seed file: {e}")
        sys.exit(1)


def ensure_categories_table(session):
    """
    Ensure finance_categories table exists (creates if not present).
    This is a reference table for POC seed data.
    Supports both old format (category_type, parent_code) and new format (type, parent).
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS finance_categories (
        code VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        type VARCHAR(50),
        category_type VARCHAR(50),
        is_active BOOLEAN DEFAULT TRUE,
        display_order INTEGER,
        parent VARCHAR(50),
        parent_code VARCHAR(50),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_finance_categories_parent 
        ON finance_categories(COALESCE(parent, parent_code));
    """
    
    try:
        session.execute(text(create_table_sql))
        session.commit()
        logger.info("Finance categories table ensured")
    except SQLAlchemyError as e:
        logger.error(f"Error creating finance_categories table: {e}")
        session.rollback()
        raise


def seed_categories(session, categories: List[Dict[str, Any]]) -> tuple[int, int, int]:
    """
    Seed finance categories with upsert logic.
    Supports both old format (category_type, parent_code) and new format (type, parent).
    
    Args:
        session: Database session
        categories: List of category dictionaries
        
    Returns:
        Tuple of (total, updated, skipped) counts
    """
    ensure_categories_table(session)
    
    total = len(categories)
    updated = 0
    skipped = 0
    
    for category in categories:
        code = category.get('code')
        if not code:
            logger.warning(f"Skipping category without code: {category.get('name', 'Unknown')}")
            skipped += 1
            continue
        
        # Support both old format (category_type, parent_code) and new format (type, parent)
        category_type = category.get('type') or category.get('category_type')
        parent = category.get('parent') or category.get('parent_code')
        # Convert null string to None
        if parent == 'null' or parent == '':
            parent = None
        
        # Upsert using ON CONFLICT DO NOTHING (PostgreSQL)
        # If record exists, skip it; otherwise insert
        upsert_sql = text("""
            INSERT INTO finance_categories 
                (code, name, description, type, category_type, is_active, display_order, parent, parent_code, updated_at)
            VALUES 
                (:code, :name, :description, :type, :category_type, :is_active, :display_order, :parent, :parent_code, NOW())
            ON CONFLICT (code) DO NOTHING
        """)
        
        try:
            result = session.execute(upsert_sql, {
                'code': code,
                'name': category.get('name', ''),
                'description': category.get('description'),
                'type': category.get('type'),
                'category_type': category.get('category_type'),
                'is_active': category.get('is_active', True),
                'display_order': category.get('display_order'),
                'parent': parent,
                'parent_code': category.get('parent_code')
            })
            
            # Check if row was inserted (affected_rows > 0) or skipped (conflict)
            if result.rowcount > 0:
                updated += 1
                logger.debug(f"Inserted category: {code} - {category.get('name')}")
            else:
                skipped += 1
                logger.debug(f"Skipped existing category: {code} - {category.get('name')}")
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting category {code}: {e}")
            session.rollback()
            skipped += 1
    
    session.commit()
    return total, updated, skipped


def seed_pilot_rows(session, pilot_rows: List[Dict[str, Any]]) -> tuple[int, int, int]:
    """
    Seed pilot P&L rows into fact_pnl_gold with upsert logic.
    Uses SELECT check before INSERT to prevent duplicates (portable approach).
    Matches on composite key: account_id, cc_id, book_id, strategy_id, trade_date.
    
    Args:
        session: Database session
        pilot_rows: List of pilot row dictionaries
        
    Returns:
        Tuple of (total, updated, skipped) counts
    """
    total = len(pilot_rows)
    updated = 0
    skipped = 0
    
    for row in pilot_rows:
        # Convert date string to date object
        trade_date_str = row.get('trade_date')
        if isinstance(trade_date_str, str):
            trade_date = date.fromisoformat(trade_date_str)
        else:
            trade_date = trade_date_str
        
        # Convert numeric strings to Decimal for precision
        daily_pnl = Decimal(str(row.get('daily_pnl', 0)))
        mtd_pnl = Decimal(str(row.get('mtd_pnl', 0)))
        ytd_pnl = Decimal(str(row.get('ytd_pnl', 0)))
        pytd_pnl = Decimal(str(row.get('pytd_pnl', 0)))
        
        # Check if row already exists (upsert logic)
        check_sql = text("""
            SELECT fact_id 
            FROM fact_pnl_gold 
            WHERE account_id = :account_id 
              AND cc_id = :cc_id 
              AND book_id = :book_id 
              AND strategy_id = :strategy_id 
              AND trade_date = :trade_date
            LIMIT 1
        """)
        
        try:
            existing = session.execute(check_sql, {
                'account_id': row.get('account_id'),
                'cc_id': row.get('cc_id'),
                'book_id': row.get('book_id'),
                'strategy_id': row.get('strategy_id'),
                'trade_date': trade_date
            }).fetchone()
            
            if existing:
                skipped += 1
                logger.debug(f"Skipped existing pilot row: {row.get('account_id')} - {trade_date}")
            else:
                # Insert new row
                insert_sql = text("""
                    INSERT INTO fact_pnl_gold 
                        (account_id, cc_id, book_id, strategy_id, trade_date, 
                         daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl)
                    VALUES 
                        (:account_id, :cc_id, :book_id, :strategy_id, :trade_date,
                         :daily_pnl, :mtd_pnl, :ytd_pnl, :pytd_pnl)
                """)
                
                session.execute(insert_sql, {
                    'account_id': row.get('account_id'),
                    'cc_id': row.get('cc_id'),
                    'book_id': row.get('book_id'),
                    'strategy_id': row.get('strategy_id'),
                    'trade_date': trade_date,
                    'daily_pnl': daily_pnl,
                    'mtd_pnl': mtd_pnl,
                    'ytd_pnl': ytd_pnl,
                    'pytd_pnl': pytd_pnl
                })
                
                updated += 1
                logger.debug(f"Inserted pilot row: {row.get('account_id')} - {trade_date}")
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting pilot row {row.get('account_id')}: {e}")
            session.rollback()
            skipped += 1
    
    session.commit()
    return total, updated, skipped


def seed_pilot_data(session, pilot_data: List[Dict[str, Any]]) -> tuple[int, int, int]:
    """
    Seed pilot data entries (category-based format) with upsert logic.
    Creates a pilot_data table to store category-based financial entries.
    
    Args:
        session: Database session
        pilot_data: List of pilot data dictionaries with category_code, amount, period, note
        
    Returns:
        Tuple of (total, updated, skipped) counts
    """
    # Ensure pilot_data table exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS pilot_data (
        id SERIAL PRIMARY KEY,
        category_code VARCHAR(50) NOT NULL,
        amount NUMERIC(18, 2) NOT NULL,
        period VARCHAR(50),
        note TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(category_code, period)
    );
    
    CREATE INDEX IF NOT EXISTS idx_pilot_data_category 
        ON pilot_data(category_code);
    """
    
    try:
        session.execute(text(create_table_sql))
        session.commit()
        logger.info("Pilot data table ensured")
    except SQLAlchemyError as e:
        logger.error(f"Error creating pilot_data table: {e}")
        session.rollback()
        raise
    
    total = len(pilot_data)
    updated = 0
    skipped = 0
    
    for entry in pilot_data:
        category_code = entry.get('category_code')
        if not category_code:
            logger.warning(f"Skipping pilot data entry without category_code")
            skipped += 1
            continue
        
        amount = Decimal(str(entry.get('amount', 0)))
        period = entry.get('period')
        note = entry.get('note')
        
        # Upsert using ON CONFLICT DO NOTHING
        upsert_sql = text("""
            INSERT INTO pilot_data 
                (category_code, amount, period, note, updated_at)
            VALUES 
                (:category_code, :amount, :period, :note, NOW())
            ON CONFLICT (category_code, period) DO NOTHING
        """)
        
        try:
            result = session.execute(upsert_sql, {
                'category_code': category_code,
                'amount': amount,
                'period': period,
                'note': note
            })
            
            if result.rowcount > 0:
                updated += 1
                logger.debug(f"Inserted pilot data: {category_code} - {period}")
            else:
                skipped += 1
                logger.debug(f"Skipped existing pilot data: {category_code} - {period}")
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting pilot data {category_code}: {e}")
            session.rollback()
            skipped += 1
    
    session.commit()
    return total, updated, skipped


def main():
    """
    Main entry point for seed manager.
    """
    logger.info("=" * 70)
    logger.info("Finance-Insight Seed Manager - Phase 3.1 Portability")
    logger.info("=" * 70)
    
    # Load seed data
    seed_file = project_root / "data" / "pilot_seed.json"
    if not seed_file.exists():
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)
    
    seed_data = load_seed_data(seed_file)
    
    # Initialize database connection
    try:
        engine = create_db_engine()
        SessionFactory = get_session_factory(engine)
        session = SessionFactory()
        
        logger.info(f"Connected to database: {get_database_url().split('@')[-1] if '@' in get_database_url() else 'local'}")
        
        # Seed categories
        categories = seed_data.get('categories', [])
        if categories:
            logger.info(f"\nSeeding {len(categories)} finance categories...")
            total_cat, updated_cat, skipped_cat = seed_categories(session, categories)
            logger.info(f"Categories: Found {total_cat}, {updated_cat} inserted, {skipped_cat} skipped (already exist)")
        else:
            logger.info("No categories to seed")
            total_cat, updated_cat, skipped_cat = 0, 0, 0
        
        # Seed pilot data (supports both old 'pilot_rows' and new 'pilot_data' format)
        pilot_rows = seed_data.get('pilot_rows', [])
        pilot_data = seed_data.get('pilot_data', [])
        
        if pilot_rows:
            logger.info(f"\nSeeding {len(pilot_rows)} pilot P&L rows (fact table format)...")
            total_rows, updated_rows, skipped_rows = seed_pilot_rows(session, pilot_rows)
            logger.info(f"Pilot Rows: Found {total_rows}, {updated_rows} inserted, {skipped_rows} skipped (already exist)")
        elif pilot_data:
            logger.info(f"\nSeeding {len(pilot_data)} pilot data entries (category-based format)...")
            total_rows, updated_rows, skipped_rows = seed_pilot_data(session, pilot_data)
            logger.info(f"Pilot Data: Found {total_rows}, {updated_rows} inserted, {skipped_rows} skipped (already exist)")
        else:
            logger.info("No pilot data to seed")
            total_rows, updated_rows, skipped_rows = 0, 0, 0
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SEED SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Categories: Found {total_cat}, {updated_cat} updated, {skipped_cat} skipped")
        logger.info(f"Pilot Rows: Found {total_rows}, {updated_rows} updated, {skipped_rows} skipped")
        logger.info("=" * 70)
        logger.info("Seed operation completed successfully!")
        
        session.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

