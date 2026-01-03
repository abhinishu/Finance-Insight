"""
Verification Script: Execution Path & Flight Recorder Logs

This script runs a full calculation (Stage 1 + Stage 2) and displays
the "Flight Recorder" logs to verify the chain of events.

It demonstrates:
1. SQL Rules execution (Stage 1a)
2. Math Rules execution (Stage 1b) with Flight Recorder logging
3. Waterfall Up aggregation (Stage 2)
4. Complete execution trace
"""

import sys
import logging
from pathlib import Path
from typing import Tuple
from io import StringIO

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import UseCase, MetadataRule
from app.services.calculator import calculate_use_case


class FlightRecorderHandler(logging.Handler):
    """Custom logging handler to capture Flight Recorder logs."""
    
    def __init__(self):
        super().__init__()
        self.flight_recorder_logs = []
        self.all_logs = []
    
    def emit(self, record):
        """Capture log records, especially Flight Recorder logs."""
        log_message = self.format(record)
        self.all_logs.append(log_message)
        
        # Capture Flight Recorder logs (MATH ENGINE logs)
        if '🧮 MATH ENGINE' in log_message:
            self.flight_recorder_logs.append(log_message)


def setup_logging() -> Tuple[FlightRecorderHandler, logging.Logger]:
    """Set up logging with Flight Recorder capture."""
    # Create custom handler
    flight_handler = FlightRecorderHandler()
    flight_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    flight_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Add console handler for real-time output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add Flight Recorder handler
    root_logger.addHandler(flight_handler)
    
    return flight_handler, root_logger


def find_use_case_with_math_rules(db: Session) -> UseCase:
    """Find a use case that has Math rules (Type 3 rules)."""
    print("=" * 80)
    print("STEP 1: Finding Use Case with Math Rules")
    print("=" * 80)
    print()
    
    # Get all use cases
    use_cases = db.query(UseCase).all()
    
    print(f"Found {len(use_cases)} use cases in database")
    print()
    
    # Check each use case for Math rules
    for use_case in use_cases:
        math_rules = db.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case.use_case_id,
            MetadataRule.rule_type == 'NODE_ARITHMETIC',
            MetadataRule.rule_expression.isnot(None)
        ).all()
        
        if math_rules:
            print(f"  ✓ Use Case: {use_case.name}")
            print(f"    ID: {use_case.use_case_id}")
            print(f"    Math Rules Found: {len(math_rules)}")
            print()
            for rule in math_rules:
                print(f"      - Node: {rule.node_id}")
                print(f"        Expression: {rule.rule_expression}")
                print(f"        Dependencies: {rule.rule_dependencies}")
            print()
            return use_case
    
    # If no Math rules found, use the first use case (will show SQL rules only)
    if use_cases:
        use_case = use_cases[0]
        print(f"  ⚠ No Math rules found. Using first use case: {use_case.name}")
        print(f"    ID: {use_case.use_case_id}")
        print()
        return use_case
    
    raise ValueError("No use cases found in database")


def run_calculation(use_case_id, db: Session) -> dict:
    """Run a full calculation and return results."""
    print("=" * 80)
    print("STEP 2: Running Full Calculation (Stage 1 + Stage 2)")
    print("=" * 80)
    print()
    print("This will execute:")
    print("  - Stage 1a: SQL Rules (Type 1/2)")
    print("  - Stage 1b: Math Rules (Type 3) with Flight Recorder logging")
    print("  - Stage 2: Waterfall Up aggregation")
    print()
    print("-" * 80)
    print()
    
    try:
        result = calculate_use_case(
            use_case_id=use_case_id,
            session=db,
            triggered_by="verification_script",
            version_tag="verify_execution_path"
        )
        
        print()
        print("-" * 80)
        print()
        print("✓ Calculation completed successfully!")
        print()
        
        return result
        
    except Exception as e:
        print()
        print("-" * 80)
        print()
        print(f"✗ Calculation failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        raise


def display_flight_recorder_logs(flight_handler: FlightRecorderHandler):
    """Display captured Flight Recorder logs in a formatted way."""
    print("=" * 80)
    print("STEP 3: Flight Recorder Logs (Math Engine Execution Trace)")
    print("=" * 80)
    print()
    
    if not flight_handler.flight_recorder_logs:
        print("  ⚠ No Flight Recorder logs captured.")
        print("     This means no Math rules (Type 3) were executed.")
        print("     The calculation may have only used SQL rules (Type 1/2).")
        print()
        return
    
    print(f"  Found {len(flight_handler.flight_recorder_logs)} Flight Recorder log entries")
    print()
    print("-" * 80)
    print()
    
    for i, log_entry in enumerate(flight_handler.flight_recorder_logs, 1):
        print(f"  [{i}] {log_entry}")
        print()
    
    print("-" * 80)
    print()


def display_execution_summary(result: dict, flight_handler: FlightRecorderHandler):
    """Display a summary of the execution."""
    print("=" * 80)
    print("STEP 4: Execution Summary")
    print("=" * 80)
    print()
    
    print(f"  Run ID: {result.get('run_id', 'N/A')}")
    print(f"  Use Case ID: {result.get('use_case_id', 'N/A')}")
    print(f"  Rules Applied: {result.get('rules_applied', 0)}")
    print(f"  Duration: {result.get('duration_ms', 0)} ms")
    print()
    
    # Count SQL vs Math rules
    sql_rules_count = result.get('rules_applied', 0) - len(flight_handler.flight_recorder_logs)
    math_rules_count = len(flight_handler.flight_recorder_logs)
    
    print("  Rule Breakdown:")
    print(f"    - SQL Rules (Type 1/2): {sql_rules_count}")
    print(f"    - Math Rules (Type 3): {math_rules_count}")
    print()
    
    # Total plug
    total_plug = result.get('total_plug', {})
    print("  Total Reconciliation Plug:")
    print(f"    - Daily: {total_plug.get('daily', '0')}")
    print(f"    - MTD: {total_plug.get('mtd', '0')}")
    print(f"    - YTD: {total_plug.get('ytd', '0')}")
    print(f"    - PYTD: {total_plug.get('pytd', '0')}")
    print()
    
    # Results summary
    adjusted_results = result.get('adjusted_results', {})
    natural_results = result.get('natural_results', {})
    
    print(f"  Results Summary:")
    print(f"    - Nodes with Natural Values: {len(natural_results)}")
    print(f"    - Nodes with Adjusted Values: {len(adjusted_results)}")
    print()
    
    # Show sample nodes
    if adjusted_results:
        print("  Sample Nodes (first 5):")
        for i, (node_id, measures) in enumerate(list(adjusted_results.items())[:5], 1):
            natural = natural_results.get(node_id, {})
            adjusted = measures
            print(f"    [{i}] Node: {node_id}")
            print(f"        Natural Daily: {natural.get('daily', '0')}")
            print(f"        Adjusted Daily: {adjusted.get('daily', '0')}")
        print()


def main():
    """Main verification function."""
    print("=" * 80)
    print("EXECUTION PATH VERIFICATION")
    print("Flight Recorder Log Analysis")
    print("=" * 80)
    print()
    
    # Set up logging
    flight_handler, logger = setup_logging()
    
    db: Session = SessionLocal()
    
    try:
        # Find use case with Math rules
        use_case = find_use_case_with_math_rules(db)
        
        # Run calculation
        result = run_calculation(use_case.use_case_id, db)
        
        # Display Flight Recorder logs
        display_flight_recorder_logs(flight_handler)
        
        # Display execution summary
        display_execution_summary(result, flight_handler)
        
        # Final status
        print("=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
        print()
        print("✓ Execution path verified successfully!")
        print("✓ Flight Recorder logs captured and displayed")
        print()
        
        if flight_handler.flight_recorder_logs:
            print("✓ Math rules were executed and logged")
        else:
            print("⚠ No Math rules were executed (only SQL rules)")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("VERIFICATION FAILED")
        print("=" * 80)
        print()
        print(f"✗ Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

