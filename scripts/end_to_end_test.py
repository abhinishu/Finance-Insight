"""
End-to-end test script: Generate data → Create use case → Calculate → Validate
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_url
from app.engine.mock_data import generate_and_load_mock_data, validate_mock_data
from app.engine.validation import run_full_validation
from app.engine.waterfall import calculate_waterfall, save_results
from app.models import UseCaseRun, RunStatus


def main():
    """Run end-to-end test."""
    print("=" * 60)
    print("Finance-Insight End-to-End Test")
    print("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Step 1: Generate mock data
        print("\n" + "=" * 60)
        print("Step 1: Generating Mock Data")
        print("=" * 60)
        summary = generate_and_load_mock_data(session, clear_existing=True)
        print(f"✓ Generated {summary['fact_rows']} fact rows")
        print(f"✓ Generated {summary['hierarchy_nodes']} hierarchy nodes")
        print(f"✓ Generated {summary['leaf_nodes']} leaf nodes")
        
        # Validate mock data
        validation = validate_mock_data(session)
        if not validation['passed']:
            print("\n✗ Mock data validation failed!")
            return 1
        print("✓ Mock data validation passed")
        
        # Step 2: Create test use case
        print("\n" + "=" * 60)
        print("Step 2: Creating Test Use Case")
        print("=" * 60)
        from scripts.create_test_use_case import create_test_use_case, add_sample_rules
        
        use_case = create_test_use_case(session, name="E2E Test Use Case", owner_id="e2e_test")
        if not use_case:
            return 1
        
        # Add a sample rule
        print("\nAdding sample rule...")
        add_sample_rules(session, use_case.use_case_id, num_rules=1)
        
        # Step 3: Run calculation
        print("\n" + "=" * 60)
        print("Step 3: Running Waterfall Calculation")
        print("=" * 60)
        
        # Create run record
        run = UseCaseRun(
            use_case_id=use_case.use_case_id,
            version_tag="e2e_test_v1",
            triggered_by="e2e_test",
            status=RunStatus.IN_PROGRESS
        )
        session.add(run)
        session.commit()
        
        # Calculate waterfall
        waterfall_results = calculate_waterfall(use_case.use_case_id, session, triggered_by="e2e_test")
        print(f"✓ Calculation completed in {waterfall_results['duration_ms']}ms")
        
        # Update run with duration
        run.calculation_duration_ms = waterfall_results['duration_ms']
        session.commit()
        
        # Save results
        result_count = save_results(run.run_id, waterfall_results, session)
        print(f"✓ Saved {result_count} result rows")
        
        # Update run status
        run.status = RunStatus.COMPLETED
        session.commit()
        
        # Step 4: Run validation
        print("\n" + "=" * 60)
        print("Step 4: Running Validation")
        print("=" * 60)
        validation_report = run_full_validation(use_case.use_case_id, session, waterfall_results=waterfall_results)
        
        if validation_report['overall_status'] == 'PASSED':
            print("✓ All validations passed!")
        else:
            print("✗ Some validations failed:")
            for name, result in validation_report['validations'].items():
                if isinstance(result, dict):
                    if 'passed' in result and not result['passed']:
                        print(f"  - {name}: {result.get('details', 'Failed')}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("End-to-End Test Summary")
        print("=" * 60)
        print(f"✓ Mock data generated and validated")
        print(f"✓ Test use case created: {use_case.use_case_id}")
        print(f"✓ Calculation completed: {waterfall_results['duration_ms']}ms")
        print(f"✓ Results saved: {result_count} rows")
        print(f"✓ Validation status: {validation_report['overall_status']}")
        
        if validation_report['overall_status'] == 'PASSED':
            print("\n" + "=" * 60)
            print("✓ End-to-End Test PASSED!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("✗ End-to-End Test FAILED!")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

