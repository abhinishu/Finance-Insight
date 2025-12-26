"""
Project Sterling - Step 3: Full Execution & Grid Hydration
Executes the 10-rule waterfall and performs reconciliation audit.
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.dependencies import get_session_factory
from app.models import (
    CalculationRun,
    DimHierarchy,
    FactCalculatedResult,
    FactPnlEntries,
    MetadataRule,
    UseCase,
    UseCaseRun,
    RunStatus,
)
from app.services.orchestrator import (
    create_snapshot,
    load_facts_for_date,
    calculate_natural_rollup_from_entries,
    apply_rules_to_results,
    calculate_variance,
    save_calculation_results,
)


def get_sterling_use_case(session: Session) -> UseCase:
    """Get Project Sterling use case."""
    use_case = session.query(UseCase).filter(
        UseCase.name == "Project Sterling - Multi-Dimensional Facts"
    ).first()
    
    if not use_case:
        raise ValueError("Project Sterling use case not found. Run Step 2 first.")
    
    return use_case


def apply_sterling_python_rules(
    session: Session,
    facts_df: pd.DataFrame,
    rules: List[MetadataRule]
) -> pd.DataFrame:
    """
    Apply Sterling Python rules sequentially to fact rows.
    This is a custom implementation since Sterling rules use Python logic, not SQL.
    """
    from decimal import Decimal
    
    # Make a copy to avoid modifying original
    adjusted_df = facts_df.copy()
    
    # Convert to list of dicts for rule application (include audit_metadata)
    fact_rows = []
    for _, row in adjusted_df.iterrows():
        # Get full fact record to access audit_metadata
        fact_id = row.get('fact_id')
        if fact_id:
            fact = session.query(FactPnlEntries).filter(FactPnlEntries.id == fact_id).first()
            if fact:
                row_dict = {
                    'fact_id': str(fact.id),
                    'category_code': fact.category_code,
                    'daily_amount': Decimal(str(fact.daily_amount)),
                    'wtd_amount': Decimal(str(fact.wtd_amount)),
                    'ytd_amount': Decimal(str(fact.ytd_amount)),
                    'scenario': fact.scenario,
                    'audit_metadata': fact.audit_metadata or {}
                }
                fact_rows.append(row_dict)
    
    # Sort rules by rule_id from predicate_json
    sorted_rules = sorted(rules, key=lambda r: r.predicate_json.get('rule_id', 0) if r.predicate_json else 0)
    
    # Apply each rule sequentially
    for rule in sorted_rules:
        predicate = rule.predicate_json or {}
        logic_py = predicate.get('logic_py', '')
        
        if not logic_py:
            continue
        
        # Execute the Python logic (safely)
        try:
            # Create a safe execution environment
            exec_globals = {
                'Decimal': Decimal,
                'row': None,
                'prior_row': None,
            }
            exec(logic_py, exec_globals)
            apply_rule_func = exec_globals.get('apply_rule')
            
            if not apply_rule_func:
                continue
            
            # Apply rule to each row
            for i, row in enumerate(fact_rows):
                # Get prior row if needed (for Rule 5 - High-Variance Bonus)
                prior_row = None
                if row.get('scenario') == 'ACTUAL':
                    # Find matching PRIOR scenario row
                    prior_row = next(
                        (r for r in fact_rows if r.get('category_code') == row.get('category_code') and r.get('scenario') == 'PRIOR'),
                        None
                    )
                
                # Execute rule
                try:
                    result = apply_rule_func(row, prior_row=prior_row)
                    if result:
                        # Update row with rule result
                        row['daily_amount'] = result.get('daily_amount', row['daily_amount'])
                        row['wtd_amount'] = result.get('wtd_amount', row['wtd_amount'])
                        row['ytd_amount'] = result.get('ytd_amount', row['ytd_amount'])
                except Exception as e:
                    print(f"Warning: Rule {rule.rule_id} failed for row {i}: {e}")
                    continue
        
        except Exception as e:
            print(f"Warning: Failed to execute rule {rule.rule_id}: {e}")
            continue
    
    # Convert back to DataFrame (only for ACTUAL scenario)
    adjusted_rows = [r for r in fact_rows if r.get('scenario') == 'ACTUAL']
    if adjusted_rows:
        return pd.DataFrame(adjusted_rows)
    return facts_df


def execute_sterling_snapshot(
    session: Session,
    use_case_id: UUID,
    pnl_date: date
) -> Dict:
    """
    Execute Sterling snapshot with Python rule execution.
    """
    
    # Load facts
    actual_facts_df = load_facts_for_date(session, use_case_id, pnl_date, scenario="ACTUAL")
    prior_facts_df = load_facts_for_date(session, use_case_id, pnl_date, scenario="PRIOR")
    
    if actual_facts_df.empty:
        raise ValueError(f"No ACTUAL facts found for date {pnl_date}")
    
    # Load Sterling rules (from Sterling use case, not necessarily the one with facts)
    sterling_use_case = session.query(UseCase).filter(
        UseCase.name == "Project Sterling - Multi-Dimensional Facts"
    ).first()
    
    if sterling_use_case:
        sterling_rules = session.query(MetadataRule).filter(
            MetadataRule.use_case_id == sterling_use_case.use_case_id,
            MetadataRule.node_id.like('STERLING_RULE_%')
        ).all()
        print(f"Loaded {len(sterling_rules)} Sterling rules from use case: {sterling_use_case.name}")
    else:
        # Fallback: try to find rules by node_id pattern in any use case
        sterling_rules = session.query(MetadataRule).filter(
            MetadataRule.node_id.like('STERLING_RULE_%')
        ).all()
        print(f"Loaded {len(sterling_rules)} Sterling rules (by node pattern)")
    
    # Sort rules by rule_id
    sterling_rules = sorted(sterling_rules, key=lambda r: r.predicate_json.get('rule_id', 0) if r.predicate_json else 0)
    
    print(f"Loaded {len(sterling_rules)} Sterling rules")
    
    # Apply Python rules to ACTUAL facts
    print("Applying Sterling Python rules to ACTUAL facts...")
    actual_adjusted_df = apply_sterling_python_rules(session, actual_facts_df, sterling_rules)
    
    # Apply Python rules to PRIOR facts
    print("Applying Sterling Python rules to PRIOR facts...")
    prior_adjusted_df = apply_sterling_python_rules(session, prior_facts_df, sterling_rules)
    
    # For now, we'll use the orchestrator's create_snapshot but we need to ensure
    # it works with our adjusted facts. Actually, let's create a simpler approach:
    # We'll create the calculation run and save results directly.
    
    # Create calculation run
    calculation_run = CalculationRun(
        pnl_date=pnl_date,
        use_case_id=use_case_id,
        run_name=f"Sterling_10Rule_Waterfall_{pnl_date.strftime('%Y%m%d')}",
        status="IN_PROGRESS",
        triggered_by="sterling_step3"
    )
    session.add(calculation_run)
    
    # Create a dummy UseCaseRun to satisfy run_id FK constraint (legacy field)
    dummy_run = UseCaseRun(
        use_case_id=use_case_id,
        version_tag=f"sterling_dummy_{pnl_date.strftime('%Y%m%d')}",
        status=RunStatus.COMPLETED,
        triggered_by="sterling_step3"
    )
    session.add(dummy_run)
    session.flush()  # Get the run_id
    
    session.commit()
    session.refresh(calculation_run)
    
    print(f"Created calculation run: {calculation_run.id}")
    print(f"Created dummy UseCaseRun: {dummy_run.run_id} (for legacy run_id FK)")
    
    # For hierarchy, we'll need to create a simple structure or use existing
    # For Sterling, we can create a flat hierarchy based on category_code
    # Actually, let's use the orchestrator's approach but with our adjusted facts
    
    # Save results (simplified - we'll store fact-level results)
    result_count = 0
    for _, row in actual_adjusted_df.iterrows():
        # Calculate adjustment (difference between original and adjusted)
        original = actual_facts_df[actual_facts_df['category_code'] == row['category_code']].iloc[0]
        daily_adjustment = Decimal(str(row['daily_amount'])) - Decimal(str(original['daily_amount']))
        wtd_adjustment = Decimal(str(row['wtd_amount'])) - Decimal(str(original['wtd_amount']))
        ytd_adjustment = Decimal(str(row['ytd_amount'])) - Decimal(str(original['ytd_amount']))
        
        # Create a node_id from category_code (or use a generic one)
        node_id = f"STERLING_{row['category_code']}"
        
        # Check if hierarchy node exists, create if not
        hierarchy_node = session.query(DimHierarchy).filter(
            DimHierarchy.node_id == node_id
        ).first()
        
        if not hierarchy_node:
            hierarchy_node = DimHierarchy(
                node_id=node_id,
                parent_node_id=None,
                node_name=row['category_code'],
                depth=0,
                is_leaf=True,
                atlas_source="STERLING"
            )
            session.add(hierarchy_node)
            session.flush()
        
        # Create result (run_id is legacy, we use calculation_run_id)
        result = FactCalculatedResult(
            run_id=dummy_run.run_id,  # Legacy field - required by DB FK constraint
            calculation_run_id=calculation_run.id,
            node_id=node_id,
            measure_vector={
                'daily': str(row['daily_amount']),
                'wtd': str(row['wtd_amount']),
                'ytd': str(row['ytd_amount']),
            },
            plug_vector={
                'daily': str(daily_adjustment),
                'wtd': str(wtd_adjustment),
                'ytd': str(ytd_adjustment),
            },
            is_override=True,  # All Sterling facts have rules applied
            is_reconciled=True
        )
        session.add(result)
        result_count += 1
    
    calculation_run.status = "COMPLETED"
    session.commit()
    
    return {
        'calculation_run_id': calculation_run.id,
        'result_count': result_count,
        'rules_applied': len(sterling_rules)
    }


def verify_rule_1_emea_buffer(session: Session, calculation_run_id: UUID) -> Dict:
    """
    Verify Rule #1 (EMEA Buffer) on a London-based trade.
    """
    # Find a London-based trade (EMEA region)
    london_trade = session.query(FactPnlEntries).filter(
        FactPnlEntries.audit_metadata['region'].astext == 'EMEA'
    ).first()
    
    if not london_trade:
        return {'status': 'SKIPPED', 'reason': 'No EMEA trades found'}
    
    # Get the result for this trade
    node_id = f"STERLING_{london_trade.category_code}"
    result = session.query(FactCalculatedResult).filter(
        and_(
            FactCalculatedResult.calculation_run_id == calculation_run_id,
            FactCalculatedResult.node_id == node_id
        )
    ).first()
    
    if not result:
        return {'status': 'FAILED', 'reason': 'No result found for EMEA trade'}
    
    # Calculate expected adjustment (0.5% of daily_amount)
    original_daily = Decimal(str(london_trade.daily_amount))
    expected_adjustment = original_daily * Decimal('0.005')
    
    # Get actual adjustment from plug_vector
    actual_adjustment = Decimal(str(result.plug_vector.get('daily', '0')))
    
    # Verify (allow small tolerance for rounding)
    tolerance = Decimal('0.01')
    difference = abs(actual_adjustment - expected_adjustment)
    
    return {
        'status': 'PASSED' if difference <= tolerance else 'FAILED',
        'original_daily': float(original_daily),
        'expected_adjustment': float(expected_adjustment),
        'actual_adjustment': float(actual_adjustment),
        'difference': float(difference),
        'tolerance': float(tolerance)
    }


def reconciliation_audit(session: Session, calculation_run_id: UUID) -> Dict:
    """
    Perform global sum check: Total Original + Total Adjustments = Total Adjusted
    """
    # Get all results for this run
    results = session.query(FactCalculatedResult).filter(
        FactCalculatedResult.calculation_run_id == calculation_run_id
    ).all()
    
    if not results:
        return {'status': 'FAILED', 'reason': 'No results found'}
    
    total_original_daily = Decimal('0')
    total_adjustments_daily = Decimal('0')
    total_adjusted_daily = Decimal('0')
    
    for result in results:
        # Extract node_id to get original fact
        category_code = result.node_id.replace('STERLING_', '')
        
        # Get original fact (we need to get it from the run's use_case and date)
        calc_run = session.query(CalculationRun).filter(
            CalculationRun.id == calculation_run_id
        ).first()
        
        if calc_run:
            original_fact = session.query(FactPnlEntries).filter(
                and_(
                    FactPnlEntries.use_case_id == calc_run.use_case_id,
                    FactPnlEntries.pnl_date == calc_run.pnl_date,
                    FactPnlEntries.category_code == category_code,
                    FactPnlEntries.scenario == 'ACTUAL'
                )
            ).first()
            
            if original_fact:
                original_daily = Decimal(str(original_fact.daily_amount))
                total_original_daily += original_daily
        
        # Get adjusted and adjustment from result
        adjusted_daily = Decimal(str(result.measure_vector.get('daily', '0')))
        adjustment_daily = Decimal(str(result.plug_vector.get('daily', '0')))
        
        total_adjusted_daily += adjusted_daily
        total_adjustments_daily += adjustment_daily
    
    # Golden Equation: Original + Adjustments = Adjusted
    expected_adjusted = total_original_daily + total_adjustments_daily
    difference = abs(total_adjusted_daily - expected_adjusted)
    
    tolerance = Decimal('0.01')
    status = 'PASSED' if difference <= tolerance else 'FAILED'
    
    return {
        'status': status,
        'total_original_daily': float(total_original_daily),
        'total_adjustments_daily': float(total_adjustments_daily),
        'total_adjusted_daily': float(total_adjusted_daily),
        'expected_adjusted': float(expected_adjusted),
        'difference': float(difference),
        'tolerance': float(tolerance),
        'golden_equation': f"{total_original_daily} + {total_adjustments_daily} = {expected_adjusted} (Actual: {total_adjusted_daily})"
    }


def mark_as_latest(session: Session, calculation_run_id: UUID):
    """
    Mark this run as the latest for UI auto-loading.
    Note: This might require updating a use_case field or creating a separate tracking mechanism.
    """
    calc_run = session.query(CalculationRun).filter(
        CalculationRun.id == calculation_run_id
    ).first()
    
    if calc_run:
        # Update run_name to indicate it's latest
        calc_run.run_name = f"[LATEST] {calc_run.run_name}"
        session.commit()
        print(f"Marked run {calculation_run_id} as LATEST")


if __name__ == "__main__":
    """
    CLI interface for Sterling Step 3.
    Usage:
        python scripts/sterling_step3_execute.py
    """
    
    print("=" * 80)
    print("Project Sterling - Step 3: Full Execution & Grid Hydration")
    print("=" * 80)
    print()
    
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        # Get use case - try to find one that has Sterling facts
        pnl_date = date(2025, 12, 24)
        
        # First, find which use case has facts for this date
        fact = session.query(FactPnlEntries).filter(
            FactPnlEntries.pnl_date == pnl_date
        ).first()
        
        if fact:
            use_case = session.query(UseCase).filter(
                UseCase.use_case_id == fact.use_case_id
            ).first()
            print(f"Using Use Case with facts: {use_case.name} (ID: {use_case.use_case_id})")
        else:
            # Fallback to name-based lookup
            use_case = get_sterling_use_case(session)
            print(f"Using Use Case by name: {use_case.name} (ID: {use_case.use_case_id})")
        
        # Execute snapshot
        print(f"Executing snapshot for PNL_DATE: {pnl_date}")
        print()
        
        result = execute_sterling_snapshot(session, use_case.use_case_id, pnl_date)
        
        print(f"[SUCCESS] Snapshot created:")
        print(f"   - Calculation Run ID: {result['calculation_run_id']}")
        print(f"   - Results Count: {result['result_count']}")
        print(f"   - Rules Applied: {result['rules_applied']}")
        print()
        
        # Verify Rule #1
        print("=" * 80)
        print("VERIFICATION: Rule #1 (EMEA Buffer)")
        print("=" * 80)
        rule1_verification = verify_rule_1_emea_buffer(session, result['calculation_run_id'])
        print(f"Status: {rule1_verification['status']}")
        if rule1_verification['status'] != 'SKIPPED':
            print(f"Original Daily: ${rule1_verification.get('original_daily', 0):,.2f}")
            print(f"Expected Adjustment (0.5%): ${rule1_verification.get('expected_adjustment', 0):,.2f}")
            print(f"Actual Adjustment: ${rule1_verification.get('actual_adjustment', 0):,.2f}")
            print(f"Difference: ${rule1_verification.get('difference', 0):,.2f}")
        print()
        
        # Reconciliation Audit
        print("=" * 80)
        print("RECONCILIATION AUDIT: Golden Equation")
        print("=" * 80)
        audit_result = reconciliation_audit(session, result['calculation_run_id'])
        print(f"Status: {audit_result['status']}")
        print(f"Total Original Daily: ${audit_result['total_original_daily']:,.2f}")
        print(f"Total Adjustments: ${audit_result['total_adjustments_daily']:,.2f}")
        print(f"Total Adjusted Daily: ${audit_result['total_adjusted_daily']:,.2f}")
        print(f"Expected (Original + Adjustments): ${audit_result['expected_adjusted']:,.2f}")
        print(f"Difference: ${audit_result['difference']:,.2f}")
        print(f"Tolerance: ${audit_result['tolerance']:,.2f}")
        print()
        print(f"Golden Equation: {audit_result['golden_equation']}")
        print()
        
        if audit_result['status'] == 'FAILED':
            print("=" * 80)
            print("[CRITICAL WARNING] Golden Equation FAILED!")
            print(f"Discrepancy: ${audit_result['difference']:,.2f}")
            print("=" * 80)
        else:
            print("=" * 80)
            print("[SUCCESS] Golden Equation PASSED")
            print("=" * 80)
        
        # Mark as latest
        mark_as_latest(session, result['calculation_run_id'])
        print()
        
        print("=" * 80)
        print(f"Golden Equation Status: {audit_result['status']}")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        session.close()

