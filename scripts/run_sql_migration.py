"""
Execute SQL migration file safely with proper transaction handling.
"""

import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine


def parse_sql_file(file_path: str) -> list[str]:
    """
    Parse SQL file into individual statements.
    Removes comments and splits by semicolons properly.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove single-line comments (-- ...)
    content = re.sub(r'--.*?$', '', content, flags=re.MULTILINE)
    
    # Remove multi-line comments (/* ... */)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Split by semicolons and clean up
    statements = []
    for statement in content.split(';'):
        statement = statement.strip()
        if statement and not statement.isspace():
            statements.append(statement)
    
    return statements


def execute_migration(file_path: str) -> int:
    """
    Execute SQL migration file.
    
    Returns:
        0 on success, 1 on error
    """
    print(f"Executing migration: {file_path}")
    print("=" * 60)
    
    try:
        statements = parse_sql_file(file_path)
        print(f"Found {len(statements)} SQL statements to execute\n")
        
        with engine.connect() as conn:
            # Begin transaction
            trans = conn.begin()
            
            try:
                for i, statement in enumerate(statements, 1):
                    # Skip empty statements
                    if not statement.strip():
                        continue
                    
                    print(f"Executing statement {i}/{len(statements)}...")
                    
                    try:
                        # Execute statement
                        conn.execute(text(statement))
                        
                        # Commit after each successful statement
                        trans.commit()
                        trans = conn.begin()  # Start new transaction for next statement
                        
                        print(f"  [OK] Statement {i} executed successfully")
                    
                    except Exception as e:
                        error_msg = str(e)
                        # Check if it's a "already exists" error - that's OK for idempotent migrations
                        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                            print(f"  [SKIP] Statement {i} - object already exists (safe to ignore)")
                            trans.rollback()
                            trans = conn.begin()  # Start new transaction
                            continue
                        else:
                            # Real error - rollback and re-raise
                            trans.rollback()
                            print(f"\n[ERROR] Error executing statement {i}: {e}")
                            print(f"Statement was:\n{statement[:200]}...")
                            raise
                
                print("\n" + "=" * 60)
                print("[OK] Migration completed successfully!")
                print("=" * 60)
                return 0
                
            except Exception as e:
                trans.rollback()
                print(f"\n[ERROR] Migration failed: {e}")
                raise
        
    except FileNotFoundError:
        print(f"[ERROR] Migration file not found: {file_path}")
        return 1
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Execute SQL migration file"
    )
    parser.add_argument(
        "migration_file",
        type=str,
        help="Path to SQL migration file (e.g., migration_006_trading_foundation.sql)"
    )
    
    args = parser.parse_args()
    
    # Resolve path
    migration_path = Path(args.migration_file)
    if not migration_path.is_absolute():
        migration_path = project_root / migration_path
    
    if not migration_path.exists():
        print(f"❌ File not found: {migration_path}")
        return 1
    
    return execute_migration(str(migration_path))


if __name__ == "__main__":
    sys.exit(main())

