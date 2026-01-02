"""
Phase 5.2: Seed Use Case 3 Business Rules
Creates business rules for the "America Cash Equity Trading" use case.

This script creates rules of different types:
- Type 1: Simple dimension filtering
- Type 2: Multi-condition filtering
- Type 2B: Arithmetic of multiple queries (FILTER_ARITHMETIC)
- Type 3: Node arithmetic operations (NODE_ARITHMETIC)
"""

import sys
import json
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.dependencies import get_session_factory
from app.models import UseCase, MetadataRule


STRUCTURE_ID = "America Cash Equity Trading Structure"


def get_use_case(session: Session) -> UseCase:
    """Get the 'America Cash Equity Trading' use case."""
    use_case = session.query(UseCase).filter(
        UseCase.name == "America Cash Equity Trading"
    ).first()
    
    if not use_case:
        raise ValueError("Use case 'America Cash Equity Trading' not found. Run seed_use_case_3_structure.py first.")
    
    return use_case


def create_type1_rule(session: Session, use_case: UseCase, node_id: str, node_name: str, 
                      dimension: str, dimension_value: str, measure: str = "daily_pnl"):
    """Create a Type 1 rule (simple dimension filter)."""
    # Check if rule already exists
    existing = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case.use_case_id,
        MetadataRule.node_id == node_id
    ).first()
    
    if existing:
        print(f"[SKIP] Rule for {node_id} ({node_name}) already exists")
        return existing
    
    # Create predicate_json (Version 1.0 for Type 1)
    predicate_json = {
        "version": "1.0",
        "rule_type": "FILTER_SIMPLE",
        "measure": measure,
        "aggregation": "SUM",
        "filters": [
            {
                "field": dimension,
                "operator": "=",
                "value": dimension_value
            }
        ]
    }
    
    # Create SQL WHERE clause
    sql_where = f"{dimension} = '{dimension_value}'"
    
    # Create logic_en
    logic_en = f"SUM({measure.upper()}) WHERE {dimension} = '{dimension_value}'"
    
    # Use raw SQL to insert with new columns (rule_type, measure_name)
    sql = text("""
        INSERT INTO metadata_rules (
            use_case_id, node_id, rule_type, measure_name,
            predicate_json, sql_where, logic_en, last_modified_by
        ) VALUES (
            :use_case_id, :node_id, :rule_type, :measure_name,
            :predicate_json, :sql_where, :logic_en, :last_modified_by
        )
    """)
    
    session.execute(sql, {
        "use_case_id": str(use_case.use_case_id),
        "node_id": node_id,
        "rule_type": "FILTER",
        "measure_name": measure,
        "predicate_json": json.dumps(predicate_json),
        "sql_where": sql_where,
        "logic_en": logic_en,
        "last_modified_by": "system"
    })
    
    print(f"[OK] Created Type 1 rule for {node_id} ({node_name}): {logic_en}")
    return None  # Return None since we're using raw SQL


def create_type2_rule(session: Session, use_case: UseCase, node_id: str, node_name: str,
                      filters: list, measure: str = "daily_pnl"):
    """Create a Type 2 rule (multi-condition filter)."""
    # Check if rule already exists
    existing = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case.use_case_id,
        MetadataRule.node_id == node_id
    ).first()
    
    if existing:
        print(f"[SKIP] Rule for {node_id} ({node_name}) already exists")
        return existing
    
    # Create predicate_json (Version 1.0 for Type 2)
    predicate_json = {
        "version": "1.0",
        "rule_type": "FILTER_MULTI",
        "measure": measure,
        "aggregation": "SUM",
        "filters": filters
    }
    
    # Create SQL WHERE clause
    where_parts = []
    for f in filters:
        if f["operator"] == "=":
            where_parts.append(f"{f['field']} = '{f['value']}'")
        elif f["operator"] == "IN":
            values = ", ".join([f"'{v}'" for v in f["values"]])
            where_parts.append(f"{f['field']} IN ({values})")
    
    sql_where = " AND ".join(where_parts)
    
    # Create logic_en
    logic_parts = []
    for f in filters:
        if f["operator"] == "=":
            logic_parts.append(f"{f['field']} = '{f['value']}'")
        elif f["operator"] == "IN":
            values = ", ".join([f"'{v}'" for v in f["values"]])
            logic_parts.append(f"{f['field']} IN ({values})")
    
    logic_en = f"SUM({measure.upper()}) WHERE {' AND '.join(logic_parts)}"
    
    # Use raw SQL to insert with new columns
    sql = text("""
        INSERT INTO metadata_rules (
            use_case_id, node_id, rule_type, measure_name,
            predicate_json, sql_where, logic_en, last_modified_by
        ) VALUES (
            :use_case_id, :node_id, :rule_type, :measure_name,
            :predicate_json, :sql_where, :logic_en, :last_modified_by
        )
    """)
    
    session.execute(sql, {
        "use_case_id": str(use_case.use_case_id),
        "node_id": node_id,
        "rule_type": "FILTER",
        "measure_name": measure,
        "predicate_json": json.dumps(predicate_json),
        "sql_where": sql_where,
        "logic_en": logic_en,
        "last_modified_by": "system"
    })
    
    print(f"[OK] Created Type 2 rule for {node_id} ({node_name}): {logic_en}")
    return None


def create_type2b_rule(session: Session, use_case: UseCase, node_id: str, node_name: str,
                       queries: list, operator: str = "+"):
    """Create a Type 2B rule (arithmetic of multiple queries)."""
    # Check if rule already exists
    existing = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case.use_case_id,
        MetadataRule.node_id == node_id
    ).first()
    
    if existing:
        print(f"[SKIP] Rule for {node_id} ({node_name}) already exists")
        return existing
    
    # Create predicate_json (Version 2.0 for Type 2B)
    query_ids = [f"query_{i+1}" for i in range(len(queries))]
    
    predicate_json = {
        "version": "2.0",
        "rule_type": "FILTER_ARITHMETIC",
        "expression": {
            "operator": operator,
            "operands": [
                {
                    "type": "query",
                    "query_id": qid
                }
                for qid in query_ids
            ]
        },
        "queries": [
            {
                "query_id": qid,
                "measure": q["measure"],
                "aggregation": "SUM",
                "filters": q["filters"]
            }
            for qid, q in zip(query_ids, queries)
        ]
    }
    
    # Create logic_en
    query_descriptions = []
    for q in queries:
        filter_parts = []
        for f in q["filters"]:
            if f["operator"] == "=":
                filter_parts.append(f"{f['field']}='{f['value']}'")
            elif f["operator"] == "IN":
                values = ", ".join([f"'{v}'" for v in f["values"]])
                filter_parts.append(f"{f['field']} IN ({values})")
        
        filter_str = " AND ".join(filter_parts)
        query_descriptions.append(f"SUM({q['measure'].upper()}) WHERE {filter_str}")
    
    # Create logic_en with proper operator
    operator_str = " + " if operator == "+" else " - " if operator == "-" else " * " if operator == "*" else " / "
    logic_en = operator_str.join(query_descriptions)
    
    # Use raw SQL to insert with new columns
    sql = text("""
        INSERT INTO metadata_rules (
            use_case_id, node_id, rule_type, measure_name,
            predicate_json, sql_where, logic_en, last_modified_by
        ) VALUES (
            :use_case_id, :node_id, :rule_type, :measure_name,
            :predicate_json, :sql_where, :logic_en, :last_modified_by
        )
    """)
    
    session.execute(sql, {
        "use_case_id": str(use_case.use_case_id),
        "node_id": node_id,
        "rule_type": "FILTER_ARITHMETIC",
        "measure_name": None,  # Type 2B uses multiple measures
        "predicate_json": json.dumps(predicate_json),
        "sql_where": "",  # Empty string for Type 2B (generated dynamically)
        "logic_en": logic_en,
        "last_modified_by": "system"
    })
    
    print(f"[OK] Created Type 2B rule for {node_id} ({node_name}): {logic_en}")
    return None


def create_type3_rule(session: Session, use_case: UseCase, node_id: str, node_name: str,
                      expression: str, dependencies: list):
    """Create a Type 3 rule (node arithmetic)."""
    # Check if rule already exists
    existing = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case.use_case_id,
        MetadataRule.node_id == node_id
    ).first()
    
    if existing:
        print(f"[SKIP] Rule for {node_id} ({node_name}) already exists")
        return existing
    
    # Use raw SQL to insert with new columns (rule_type, rule_expression, rule_dependencies)
    sql = text("""
        INSERT INTO metadata_rules (
            use_case_id, node_id, rule_type, measure_name,
            rule_expression, rule_dependencies,
            predicate_json, sql_where, logic_en, last_modified_by
        ) VALUES (
            :use_case_id, :node_id, :rule_type, :measure_name,
            :rule_expression, :rule_dependencies,
            :predicate_json, :sql_where, :logic_en, :last_modified_by
        )
    """)
    
    session.execute(sql, {
        "use_case_id": str(use_case.use_case_id),
        "node_id": node_id,
        "rule_type": "NODE_ARITHMETIC",
        "measure_name": None,
        "rule_expression": expression,  # e.g., "NODE_3 - NODE_4"
        "rule_dependencies": json.dumps(dependencies),  # JSONB array
        "predicate_json": None,
        "sql_where": "",  # Empty string for Type 3 (not used)
        "logic_en": f"{node_name} = {expression}",
        "last_modified_by": "system"
    })
    
    print(f"[OK] Created Type 3 rule for {node_id} ({node_name}): {expression}")
    return None


def create_all_rules(session: Session, use_case: UseCase):
    """Create all business rules for Use Case 3."""
    print("\nCreating business rules...")
    print("="*70)
    
    # Type 1: Node 2 - CORE Products
    create_type1_rule(
        session, use_case,
        node_id="NODE_2",
        node_name="CORE Products",
        dimension="product_line",
        dimension_value="CORE Products",
        measure="daily_pnl"
    )
    
    # Type 1: Node 11 - ETF Amber
    create_type1_rule(
        session, use_case,
        node_id="NODE_11",
        node_name="ETF Amber",
        dimension="strategy",
        dimension_value="ETF Amer",  # Note: "ETF Amer" not "ETF Amber"
        measure="daily_pnl"
    )
    
    # Type 1: Node 12 - MSET
    create_type1_rule(
        session, use_case,
        node_id="NODE_12",
        node_name="MSET",
        dimension="process_1",
        dimension_value="MSET",
        measure="daily_pnl"
    )
    
    # Type 2: Node 10 - CRB
    create_type2_rule(
        session, use_case,
        node_id="NODE_10",
        node_name="CRB",
        filters=[
            {"field": "strategy", "operator": "=", "value": "CORE"},
            {"field": "book", "operator": "IN", "values": ["MSAL", "ETFUS", "Central Risk Book", "CRB Risk"]}
        ],
        measure="daily_pnl"
    )
    
    # Type 2: Node 5 - Commissions (Non Swap)
    create_type2_rule(
        session, use_case,
        node_id="NODE_5",
        node_name="Commissions (Non Swap)",
        filters=[
            {"field": "strategy", "operator": "=", "value": "CORE"}
        ],
        measure="daily_commission"
    )
    
    # Type 2: Node 6 - Swap Commission
    create_type2_rule(
        session, use_case,
        node_id="NODE_6",
        node_name="Swap Commission",
        filters=[
            {"field": "strategy", "operator": "=", "value": "CORE"},
            {"field": "process_2", "operator": "IN", "values": ["SWAP COMMISSION", "SD COMMISSION"]}
        ],
        measure="daily_trade"
    )
    
    # Type 2: Node 9 - Inventory Management
    create_type2_rule(
        session, use_case,
        node_id="NODE_9",
        node_name="Inventory Management",
        filters=[
            {"field": "strategy", "operator": "=", "value": "CORE"},
            {"field": "process_2", "operator": "=", "value": "Inventory Management"}
        ],
        measure="daily_pnl"
    )
    
    # Type 2B: Node 4 - Commissions (arithmetic of two queries)
    create_type2b_rule(
        session, use_case,
        node_id="NODE_4",
        node_name="Commissions",
        queries=[
            {
                "measure": "daily_commission",
                "filters": [
                    {"field": "strategy", "operator": "=", "value": "CORE"}
                ]
            },
            {
                "measure": "daily_trade",
                "filters": [
                    {"field": "strategy", "operator": "=", "value": "CORE"},
                    {"field": "process_2", "operator": "IN", "values": ["SWAP COMMISSION", "SD COMMISSION"]}
                ]
            }
        ],
        operator="+"
    )
    
    # Type 3: Node 7 - Trading (NODE_3 - NODE_4)
    create_type3_rule(
        session, use_case,
        node_id="NODE_7",
        node_name="Trading",
        expression="NODE_3 - NODE_4",
        dependencies=["NODE_3", "NODE_4"]
    )
    
    # Type 3: Node 8 - Facilitations (NODE_7 - NODE_9)
    create_type3_rule(
        session, use_case,
        node_id="NODE_8",
        node_name="Facilitations",
        expression="NODE_7 - NODE_9",
        dependencies=["NODE_7", "NODE_9"]
    )
    
    session.commit()
    print("\n[OK] All rules created successfully")


def main():
    """Main execution function."""
    print("="*70)
    print("Phase 5.2: Seed Use Case 3 Business Rules")
    print("="*70)
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        # Get use case
        use_case = get_use_case(session)
        print(f"Use Case: {use_case.name} (ID: {use_case.use_case_id})")
        
        # Create all rules
        create_all_rules(session, use_case)
        
        print("\n" + "="*70)
        print("[SUCCESS] Use Case 3 business rules created successfully!")
        print("="*70)
        print("\nNext step: Run seed_use_case_3_data.py to create fact data")
        
        return 0
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Failed to create rules: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

