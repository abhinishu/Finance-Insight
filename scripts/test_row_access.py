"""
Test script to verify SQLAlchemy Row object access patterns
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import get_db
from app.models import MetadataRule
from uuid import UUID as PyUUID

# Test how Row objects are accessed
def test_row_access():
    db = next(get_db())
    
    # Query with explicit column selection
    rules_data = db.query(
        MetadataRule.node_id,
        MetadataRule.rule_id,
        MetadataRule.logic_en,
        MetadataRule.sql_where,
        MetadataRule.rule_type,
        MetadataRule.rule_expression,
        MetadataRule.rule_dependencies
    ).filter(
        MetadataRule.use_case_id == PyUUID('fce60983-0328-496b-b6e1-34249ec5aa5a')
    ).all()
    
    print(f"Found {len(rules_data)} rules")
    
    for r in rules_data:
        print(f"\n--- Rule for node: {r.node_id} ---")
        print(f"Type of r: {type(r)}")
        print(f"Has _mapping: {hasattr(r, '_mapping')}")
        print(f"Has _asdict: {hasattr(r, '_asdict')}")
        
        # Try different access patterns
        try:
            print(f"r.node_id (attribute): {r.node_id}")
            print(f"r.rule_type (attribute): {r.rule_type}")
            print(f"r.rule_expression (attribute): {r.rule_expression}")
        except Exception as e:
            print(f"Attribute access failed: {e}")
        
        # Try mapping access
        if hasattr(r, '_mapping'):
            print(f"r._mapping: {r._mapping}")
            print(f"r._mapping['rule_type']: {r._mapping.get('rule_type')}")
            print(f"r._mapping['rule_expression']: {r._mapping.get('rule_expression')}")
        
        # Try asdict
        if hasattr(r, '_asdict'):
            d = r._asdict()
            print(f"r._asdict()['rule_type']: {d.get('rule_type')}")
            print(f"r._asdict()['rule_expression']: {d.get('rule_expression')}")
        
        # Try index access
        try:
            print(f"r[0] (node_id): {r[0]}")
            print(f"r[4] (rule_type): {r[4]}")
            print(f"r[5] (rule_expression): {r[5]}")
        except Exception as e:
            print(f"Index access failed: {e}")
        
        break  # Only test first rule

if __name__ == "__main__":
    test_row_access()

