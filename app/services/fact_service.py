"""
Fact Service - Data Access Layer for P&L Facts
Ensures strict use case isolation to prevent data leakage.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.models import FactPnlEntries, FactPnlGold


def load_facts_for_use_case(
    session: Session,
    use_case_id: UUID,
    filters: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Load fact data from fact_pnl_entries table with STRICT use_case_id filtering.
    
    This function ensures zero data leakage between use cases by mandating
    use_case_id as a required parameter.
    
    Args:
        session: SQLAlchemy session
        use_case_id: REQUIRED use case ID - filters facts to this use case only
        filters: Optional dictionary with filters like {category_code: [...], pnl_date: [...]}
    
    Returns:
        Pandas DataFrame with fact rows for the specified use case only
        Columns: category_code, daily_amount, wtd_amount, ytd_amount (mapped to daily_pnl, mtd_pnl, ytd_pnl)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # CRITICAL: Mandatory use_case_id filter - no exceptions
    query = session.query(FactPnlEntries).filter(
        FactPnlEntries.use_case_id == use_case_id
    )
    
    # CRITICAL: Filter for ACTUAL scenario only (exclude PRIOR to prevent confusion)
    # If UI shows $0.00, it's likely because aggregator is confused by PRIOR rows
    query = query.filter(FactPnlEntries.scenario == 'ACTUAL')
    logger.info(f"fact_service: Filtering for scenario='ACTUAL' only")
    
    # Apply additional filters if provided
    if filters:
        if 'category_code' in filters:
            query = query.filter(FactPnlEntries.category_code.in_(filters['category_code']))
        if 'pnl_date' in filters:
            query = query.filter(FactPnlEntries.pnl_date == filters['pnl_date'])
        if 'scenario' in filters:
            # Override default ACTUAL filter if explicitly provided
            query = query.filter(FactPnlEntries.scenario == filters['scenario'])
    
    # Count check for verification
    row_count = query.count()
    logger.info(f"fact_service: Loading {row_count} rows from fact_pnl_entries for use_case_id: {use_case_id}")
    
    # Load into DataFrame
    facts = query.all()
    
    # Convert to DataFrame with correct column mapping
    data = []
    for fact in facts:
        data.append({
            'fact_id': fact.id,
            'category_code': fact.category_code,
            'pnl_date': fact.pnl_date,
            'use_case_id': fact.use_case_id,
            'scenario': fact.scenario,
            # CRITICAL: Map fact_pnl_entries columns to standard names
            'daily_amount': Decimal(str(fact.daily_amount)),
            'wtd_amount': Decimal(str(fact.wtd_amount)),
            'ytd_amount': Decimal(str(fact.ytd_amount)),
            # Map to daily_pnl, mtd_pnl, ytd_pnl for compatibility with calculate_natural_rollup
            'daily_pnl': Decimal(str(fact.daily_amount)),  # daily_amount -> daily_pnl
            'mtd_pnl': Decimal(str(fact.wtd_amount)),      # wtd_amount -> mtd_pnl
            'ytd_pnl': Decimal(str(fact.ytd_amount)),      # ytd_amount -> ytd_pnl
            'pytd_pnl': Decimal('0'),  # Not available in fact_pnl_entries
        })
    
    df = pd.DataFrame(data)
    
    # Ensure Decimal types are preserved
    if not df.empty:
        df['daily_amount'] = df['daily_amount'].apply(lambda x: Decimal(str(x)))
        df['wtd_amount'] = df['wtd_amount'].apply(lambda x: Decimal(str(x)))
        df['ytd_amount'] = df['ytd_amount'].apply(lambda x: Decimal(str(x)))
        df['daily_pnl'] = df['daily_pnl'].apply(lambda x: Decimal(str(x)))
        df['mtd_pnl'] = df['mtd_pnl'].apply(lambda x: Decimal(str(x)))
        df['ytd_pnl'] = df['ytd_pnl'].apply(lambda x: Decimal(str(x)))
        
        # Verification: Check total P&L and verify use_case_id isolation
        total_daily = df['daily_pnl'].sum()
        unique_use_cases = df['use_case_id'].unique()
        logger.info(f"fact_service: Loaded {len(df)} rows, total daily_pnl: {total_daily}")
        logger.info(f"fact_service: Unique use_case_ids in result: {[str(uc) for uc in unique_use_cases]}")
        
        # CRITICAL: Verify isolation - should only have one use_case_id
        if len(unique_use_cases) > 1:
            logger.error(f"fact_service: DATA LEAKAGE DETECTED! Multiple use_case_ids found: {[str(uc) for uc in unique_use_cases]}")
        elif len(unique_use_cases) == 1 and str(unique_use_cases[0]) != str(use_case_id):
            logger.error(f"fact_service: DATA LEAKAGE DETECTED! Expected use_case_id {use_case_id}, got {unique_use_cases[0]}")
        else:
            logger.info(f"fact_service: ✓ Use case isolation verified - all rows belong to use_case_id: {use_case_id}")
    
    return df


def load_facts_gold_for_structure(
    session: Session,
    structure_id: str,
    leaf_cc_ids: List[str],
    filters: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Load fact data from fact_pnl_gold table filtered by hierarchy leaf nodes.
    
    This function filters by cc_id values from the hierarchy to ensure
    only facts relevant to the current structure are loaded.
    
    Args:
        session: SQLAlchemy session
        structure_id: Atlas structure identifier (for logging)
        leaf_cc_ids: List of leaf node IDs (cc_ids) from the hierarchy
        filters: Optional dictionary with additional filters
    
    Returns:
        Pandas DataFrame with fact rows filtered by cc_ids
    """
    import logging
    logger = logging.getLogger(__name__)
    
    query = session.query(FactPnlGold)
    
    # CRITICAL: Filter by leaf cc_ids from hierarchy
    if leaf_cc_ids:
        query = query.filter(FactPnlGold.cc_id.in_(leaf_cc_ids))
        logger.info(f"fact_service: Filtering fact_pnl_gold by {len(leaf_cc_ids)} leaf cc_ids for structure_id: {structure_id}")
    else:
        logger.warning(f"fact_service: No leaf_cc_ids provided for structure_id {structure_id}, loading all fact_pnl_gold")
    
    # Apply additional filters if provided
    if filters:
        if 'account_id' in filters:
            query = query.filter(FactPnlGold.account_id.in_(filters['account_id']))
        if 'book_id' in filters:
            query = query.filter(FactPnlGold.book_id.in_(filters['book_id']))
        if 'strategy_id' in filters:
            query = query.filter(FactPnlGold.strategy_id.in_(filters['strategy_id']))
    
    # Count check for verification
    row_count = query.count()
    logger.info(f"fact_service: Loading {row_count} rows from fact_pnl_gold for structure_id: {structure_id}")
    
    # Load into DataFrame
    facts = query.all()
    
    # Convert to DataFrame
    data = []
    for fact in facts:
        data.append({
            'fact_id': fact.fact_id,
            'account_id': fact.account_id,
            'cc_id': fact.cc_id,
            'book_id': fact.book_id,
            'strategy_id': fact.strategy_id,
            'trade_date': fact.trade_date,
            'daily_pnl': Decimal(str(fact.daily_pnl)),
            'mtd_pnl': Decimal(str(fact.mtd_pnl)),
            'ytd_pnl': Decimal(str(fact.ytd_pnl)),
            'pytd_pnl': Decimal(str(fact.pytd_pnl)),
        })
    
    df = pd.DataFrame(data)
    
    # Ensure Decimal types are preserved
    if not df.empty:
        df['daily_pnl'] = df['daily_pnl'].apply(lambda x: Decimal(str(x)))
        df['mtd_pnl'] = df['mtd_pnl'].apply(lambda x: Decimal(str(x)))
        df['ytd_pnl'] = df['ytd_pnl'].apply(lambda x: Decimal(str(x)))
        df['pytd_pnl'] = df['pytd_pnl'].apply(lambda x: Decimal(str(x)))
        
        # Verification: Check total P&L
        total_daily = df['daily_pnl'].sum()
        logger.info(f"fact_service: Loaded {len(df)} rows from fact_pnl_gold, total daily_pnl: {total_daily}")
    
    return df


# DEPRECATED: Use unified_pnl_service.get_unified_pnl() instead
def get_baseline_pnl(
    session: Session,
    use_case_id: UUID,
    pnl_date: Optional[str] = None,
    scenario: str = 'ACTUAL'
) -> Dict[str, Decimal]:
    """
    DEPRECATED: Use app.services.unified_pnl_service.get_unified_pnl() instead.
    
    This function is kept for backward compatibility only.
    The unified_pnl_service is the SINGLE SOURCE OF TRUTH for P&L data.
    """
    from app.services.unified_pnl_service import get_unified_pnl
    return get_unified_pnl(session, use_case_id, pnl_date=pnl_date, scenario=scenario)


# DEPRECATED: Use unified_pnl_service.get_unified_pnl() instead
def get_latest_pnl(
    session: Session,
    use_case_id: UUID,
    scenario: str = 'ACTUAL'
) -> Dict[str, Decimal]:
    """
    DEPRECATED: Use app.services.unified_pnl_service.get_unified_pnl() instead.
    
    This function is kept for backward compatibility only.
    """
    from app.services.unified_pnl_service import get_unified_pnl
    return get_unified_pnl(session, use_case_id, pnl_date=None, scenario=scenario)


def verify_reconciliation(
    session: Session,
    use_case_id: UUID,
    calculation_run_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Verify reconciliation between fact_pnl_entries (Raw) and fact_calculated_results (Adjusted).
    
    Financial Guardrail: If the sum of fact_pnl_entries (Raw) does not match the sum of
    fact_calculated_results (Adjusted) before rules are applied, log a RECONCILIATION_ERROR.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Use case UUID
        calculation_run_id: Optional calculation run ID (if None, uses latest)
    
    Returns:
        Dictionary with reconciliation status and details
    """
    import logging
    from app.models import FactCalculatedResult, CalculationRun
    from app.services.unified_pnl_service import get_unified_pnl
    logger = logging.getLogger(__name__)
    
    # Get raw totals from fact_pnl_entries using unified_pnl_service (SINGLE SOURCE OF TRUTH)
    raw_totals = get_unified_pnl(session, use_case_id, pnl_date=None, scenario='ACTUAL')
    
    # Get adjusted totals from fact_calculated_results
    if calculation_run_id:
        calc_run = session.query(CalculationRun).filter(
            CalculationRun.id == calculation_run_id,
            CalculationRun.use_case_id == use_case_id
        ).first()
    else:
        # Get latest calculation run
        calc_run = session.query(CalculationRun).filter(
            CalculationRun.use_case_id == use_case_id,
            CalculationRun.status == 'COMPLETED'
        ).order_by(CalculationRun.executed_at.desc()).first()
    
    adjusted_totals = {
        'daily_pnl': Decimal('0'),
        'mtd_pnl': Decimal('0'),
        'ytd_pnl': Decimal('0'),
    }
    
    if calc_run:
        # Sum all calculated results for this run
        results = session.query(FactCalculatedResult).filter(
            FactCalculatedResult.calculation_run_id == calc_run.id
        ).all()
        
        for result in results:
            measure_vector = result.measure_vector or {}
            adjusted_totals['daily_pnl'] += Decimal(str(measure_vector.get('daily', 0)))
            adjusted_totals['mtd_pnl'] += Decimal(str(measure_vector.get('wtd', measure_vector.get('mtd', 0))))
            adjusted_totals['ytd_pnl'] += Decimal(str(measure_vector.get('ytd', 0)))
    else:
        # No calculation run - adjusted equals raw (no rules applied)
        adjusted_totals = raw_totals.copy()
    
    # Compare raw vs adjusted (before rules, they should match)
    # Note: After rules, adjusted may differ due to overrides
    daily_diff = abs(raw_totals['daily_pnl'] - adjusted_totals['daily_pnl'])
    mtd_diff = abs(raw_totals['mtd_pnl'] - adjusted_totals['mtd_pnl'])
    ytd_diff = abs(raw_totals['ytd_pnl'] - adjusted_totals['ytd_pnl'])
    
    tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding
    
    reconciliation_status = {
        'raw_totals': raw_totals,
        'adjusted_totals': adjusted_totals,
        'differences': {
            'daily': daily_diff,
            'mtd': mtd_diff,
            'ytd': ytd_diff,
        },
        'is_reconciled': daily_diff <= tolerance and mtd_diff <= tolerance and ytd_diff <= tolerance,
        'calculation_run_id': str(calc_run.id) if calc_run else None,
    }
    
    if not reconciliation_status['is_reconciled']:
        logger.error(
            f"RECONCILIATION_ERROR: Use Case {use_case_id} - "
            f"Raw Daily: {raw_totals['daily_pnl']}, Adjusted Daily: {adjusted_totals['daily_pnl']}, "
            f"Difference: {daily_diff}"
        )
    
    return reconciliation_status
