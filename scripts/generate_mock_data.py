"""
Script to generate and load mock data into the Finance-Insight database.
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


def main():
    """Main function to generate and load mock data."""
    print("=" * 60)
    print("Finance-Insight Mock Data Generation")
    print("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    print(f"\nConnecting to database...")
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Generate and load data
        print("\nGenerating and loading mock data...")
        summary = generate_and_load_mock_data(session, clear_existing=True)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Data Generation Summary")
        print("=" * 60)
        print(f"Fact rows generated: {summary['fact_rows']}")
        print(f"Hierarchy nodes generated: {summary['hierarchy_nodes']}")
        print(f"Leaf nodes: {summary['leaf_nodes']}")
        print(f"\nDate range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"\nValue ranges:")
        print(f"  Daily P&L: {summary['value_ranges']['daily_pnl']['min']} to {summary['value_ranges']['daily_pnl']['max']}")
        print(f"  MTD P&L: {summary['value_ranges']['mtd_pnl']['min']} to {summary['value_ranges']['mtd_pnl']['max']}")
        print(f"  YTD P&L: {summary['value_ranges']['ytd_pnl']['min']} to {summary['value_ranges']['ytd_pnl']['max']}")
        
        # Validate data
        print("\n" + "=" * 60)
        print("Validating mock data...")
        print("=" * 60)
        validation = validate_mock_data(session)
        
        for check_name, check_result in validation['checks'].items():
            status = "✓ PASS" if check_result.get('passed', False) else "✗ FAIL"
            print(f"\n{status} - {check_name}")
            if 'expected' in check_result:
                print(f"  Expected: {check_result['expected']}")
            if 'actual' in check_result:
                print(f"  Actual: {check_result['actual']}")
            if 'unmapped' in check_result and check_result['unmapped']:
                print(f"  Unmapped CC IDs: {check_result['unmapped']}")
        
        if validation['passed']:
            print("\n" + "=" * 60)
            print("✓ All validation checks passed!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("✗ Some validation checks failed!")
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

