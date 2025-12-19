"""
CLI script to run waterfall calculation for a use case.
"""

import argparse
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_url
from app.engine.validation import run_full_validation
from app.engine.waterfall import calculate_waterfall, save_results
from app.models import UseCase, UseCaseRun, RunStatus


def main():
    """Main function to run waterfall calculation."""
    parser = argparse.ArgumentParser(description='Run waterfall calculation for a use case')
    parser.add_argument('--use-case-id', type=str, required=True, help='Use case UUID')
    parser.add_argument('--version-tag', type=str, help='Version tag for this run (auto-generated if not provided)')
    parser.add_argument('--triggered-by', type=str, default='cli', help='User ID who triggered the calculation')
    parser.add_argument('--skip-validation', action='store_true', help='Skip validation after calculation')
    
    args = parser.parse_args()
    
    try:
        use_case_id = UUID(args.use_case_id)
    except ValueError:
        print(f"Error: Invalid use case ID format: {args.use_case_id}")
        return 1
    
    print("=" * 60)
    print("Finance-Insight Waterfall Calculation")
    print("=" * 60)
    print(f"Use Case ID: {use_case_id}")
    print(f"Triggered By: {args.triggered_by}")
    
    # Get database URL
    db_url = get_database_url()
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verify use case exists
        use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if not use_case:
            print(f"\nError: Use case {use_case_id} not found.")
            return 1
        
        print(f"Use Case: {use_case.name}")
        print(f"Status: {use_case.status}")
        
        # Generate version tag if not provided
        version_tag = args.version_tag
        if not version_tag:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            version_tag = f"run_{timestamp}"
        
        print(f"Version Tag: {version_tag}")
        
        # Step 1: Create use case run record
        print("\nStep 1: Creating run record...")
        run = UseCaseRun(
            use_case_id=use_case_id,
            version_tag=version_tag,
            triggered_by=args.triggered_by,
            status=RunStatus.IN_PROGRESS
        )
        session.add(run)
        session.commit()
        print(f"✓ Run record created: {run.run_id}")
        
        # Step 2: Run waterfall calculation
        print("\nStep 2: Running waterfall calculation...")
        waterfall_results = calculate_waterfall(use_case_id, session, triggered_by=args.triggered_by)
        print(f"✓ Calculation completed in {waterfall_results['duration_ms']}ms")
        print(f"  - Nodes processed: {len(waterfall_results['results'])}")
        print(f"  - Override nodes: {len(waterfall_results.get('override_nodes', []))}")
        
        # Step 3: Update run record with duration
        run.calculation_duration_ms = waterfall_results['duration_ms']
        session.commit()
        
        # Step 4: Save results
        print("\nStep 3: Saving results...")
        result_count = save_results(run.run_id, waterfall_results, session)
        print(f"✓ Saved {result_count} result rows")
        
        # Step 5: Run validation
        if not args.skip_validation:
            print("\nStep 4: Running validation...")
            validation_report = run_full_validation(use_case_id, session, waterfall_results=waterfall_results)
            
            if validation_report['overall_status'] == 'PASSED':
                print("✓ All validations passed!")
            else:
                print("✗ Some validations failed:")
                for name, result in validation_report['validations'].items():
                    if isinstance(result, dict):
                        if 'passed' in result and not result['passed']:
                            print(f"  - {name}: {result.get('details', 'Failed')}")
                        elif isinstance(result, dict):
                            for key, value in result.items():
                                if isinstance(value, dict) and 'passed' in value and not value['passed']:
                                    print(f"  - {name}.{key}: {value.get('details', 'Failed')}")
        else:
            print("\nStep 4: Validation skipped (--skip-validation flag)")
        
        # Step 6: Update run status
        print("\nStep 5: Updating run status...")
        run.status = RunStatus.COMPLETED
        session.commit()
        print("✓ Run status updated to COMPLETED")
        
        # Print summary
        print("\n" + "=" * 60)
        print("Calculation Summary")
        print("=" * 60)
        print(f"Run ID: {run.run_id}")
        print(f"Version Tag: {version_tag}")
        print(f"Duration: {waterfall_results['duration_ms']}ms")
        print(f"Result Rows: {result_count}")
        print(f"Override Nodes: {len(waterfall_results.get('override_nodes', []))}")
        
        # Show root values
        root_results = waterfall_results['results'].get('ROOT', {})
        if root_results:
            print(f"\nRoot Values:")
            print(f"  Daily P&L: {root_results.get('daily', 0)}")
            print(f"  MTD P&L: {root_results.get('mtd', 0)}")
            print(f"  YTD P&L: {root_results.get('ytd', 0)}")
            print(f"  PYTD P&L: {root_results.get('pytd', 0)}")
        
        print("\n" + "=" * 60)
        print("Calculation completed successfully!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\nError during calculation: {e}")
        import traceback
        traceback.print_exc()
        
        # Update run status to FAILED
        try:
            if 'run' in locals():
                run.status = RunStatus.FAILED
                session.commit()
        except:
            pass
        
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

