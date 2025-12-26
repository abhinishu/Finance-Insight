"""
Project Sterling - Step 2: Multi-Measure Waterfall Calibration
Creates 10 business rules with Python logic for fact_pnl_entries transformation.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_session_factory
from app.models import (
    DimHierarchy,
    FactPnlEntries,
    MetadataRule,
    UseCase,
    UseCaseStatus,
)


def get_sterling_use_case(session: Session) -> UseCase:
    """Get or create Project Sterling use case."""
    use_case = session.query(UseCase).filter(
        UseCase.name == "Project Sterling - Multi-Dimensional Facts"
    ).first()
    
    if use_case is None:
        # Create use case
        use_case = UseCase(
            name="Project Sterling - Multi-Dimensional Facts",
            description="High-complexity dataset for F2B testing with multi-measure waterfall calibration",
            owner_id="sterling_import",
            atlas_structure_id="Mock Atlas Structure v1",  # Will be updated to Legal Entity > Region > Strategy > Book
            status=UseCaseStatus.ACTIVE
        )
        session.add(use_case)
        session.flush()
        print(f"Created use case: {use_case.use_case_id}")
    
    return use_case


def get_or_create_sterling_nodes(session: Session, use_case: UseCase) -> Dict[int, str]:
    """
    Get or create placeholder nodes for Sterling rules.
    Since the constraint allows only one rule per node, we create 10 separate nodes.
    Returns a dictionary mapping rule_id -> node_id
    """
    node_mapping = {}
    
    # Try to find ROOT node first (as parent)
    root_node = session.query(DimHierarchy).filter(
        DimHierarchy.node_id == 'ROOT',
        DimHierarchy.atlas_source == use_case.atlas_structure_id
    ).first()
    
    parent_id = 'ROOT' if root_node else None
    
    # Create 10 placeholder nodes (one per rule)
    for rule_num in range(1, 11):
        node_id = f'STERLING_RULE_{rule_num:03d}'
        existing = session.query(DimHierarchy).filter(
            DimHierarchy.node_id == node_id
        ).first()
        
        if not existing:
            node = DimHierarchy(
                node_id=node_id,
                parent_node_id=parent_id,
                node_name=f'Sterling Rule {rule_num} (Fact-Level)',
                depth=1 if parent_id else 0,
                is_leaf=True,  # These are leaf nodes (fact-level rules)
                atlas_source=use_case.atlas_structure_id
            )
            session.add(node)
            node_mapping[rule_num] = node_id
        else:
            node_mapping[rule_num] = node_id
    
    session.flush()
    return node_mapping


def create_sterling_rules(session: Session, use_case_id: UUID, node_mapping: Dict[int, str]) -> Dict:
    """
    Create the 10 Sterling rules with logic_en and logic_py.
    
    Rules are stored with:
    - logic_en: English description
    - predicate_json: Contains logic_py and metadata
    - sql_where: SQL filter for fact_pnl_entries (for compatibility)
    """
    
    # Get a root node for rules (or create a generic one)
    # For Sterling, we'll apply rules at the fact level, not hierarchy level
    # We'll use a special node_id pattern: "STERLING_RULE_{N}"
    
    rules_data = [
        {
            "rule_id": 1,
            "name": "Region Buffer",
            "logic_en": "If Region == 'EMEA', apply a +0.5% FX Buffer to daily, wtd, and ytd.",
            "logic_py": """
def apply_rule(row):
    if row.get('audit_metadata', {}).get('region') == 'EMEA':
        daily = Decimal(str(row['daily_amount']))
        wtd = Decimal(str(row['wtd_amount']))
        ytd = Decimal(str(row['ytd_amount']))
        buffer = Decimal('0.005')  # 0.5%
        return {
            'daily_amount': daily * (Decimal('1') + buffer),
            'wtd_amount': wtd * (Decimal('1') + buffer),
            'ytd_amount': ytd * (Decimal('1') + buffer)
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'region' = 'EMEA')",
            "node_id": None  # Will be set from node_mapping
        },
        {
            "rule_id": 2,
            "name": "Strategy Haircut",
            "logic_en": "If Strategy == 'MARKET_MAKING', apply a 2% Liquidity Charge (negative) to all measures.",
            "logic_py": """
def apply_rule(row):
    if row.get('audit_metadata', {}).get('strategy') == 'MARKET_MAKING':
        daily = Decimal(str(row['daily_amount']))
        wtd = Decimal(str(row['wtd_amount']))
        ytd = Decimal(str(row['ytd_amount']))
        haircut = Decimal('0.02')  # 2%
        return {
            'daily_amount': daily * (Decimal('1') - haircut),
            'wtd_amount': wtd * (Decimal('1') - haircut),
            'ytd_amount': ytd * (Decimal('1') - haircut)
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'strategy' = 'MARKET_MAKING')",
            "node_id": None
        },
        {
            "rule_id": 3,
            "name": "NYC Tech Tax",
            "logic_en": "If Region == 'AMER' and Book contains 'NYC', subtract a flat $10,000 from daily.",
            "logic_py": """
def apply_rule(row):
    metadata = row.get('audit_metadata', {})
    if metadata.get('region') == 'AMER' and 'NYC' in str(metadata.get('book', '')):
        daily = Decimal(str(row['daily_amount']))
        return {
            'daily_amount': daily - Decimal('10000'),
            'wtd_amount': Decimal(str(row['wtd_amount'])),
            'ytd_amount': Decimal(str(row['ytd_amount']))
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'region' = 'AMER' AND fpe.audit_metadata->>'book' LIKE '%NYC%')",
            "node_id": None
        },
        {
            "rule_id": 4,
            "name": "Sarah's Cap",
            "logic_en": "If Risk Officer == 'LDN_001', cap the daily_amount at $500,000 (if it exceeds, subtract the difference).",
            "logic_py": """
def apply_rule(row):
    if row.get('audit_metadata', {}).get('risk_officer') == 'LDN_001':
        daily = Decimal(str(row['daily_amount']))
        cap = Decimal('500000')
        if daily > cap:
            adjustment = daily - cap
            return {
                'daily_amount': cap,
                'wtd_amount': Decimal(str(row['wtd_amount'])) - adjustment,
                'ytd_amount': Decimal(str(row['ytd_amount'])) - adjustment
            }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'risk_officer' = 'LDN_001')",
            "node_id": None
        },
        {
            "rule_id": 5,
            "name": "High-Variance Bonus",
            "logic_en": "If (Actual_Daily - Prior_Daily) > 100000, add a 1% 'Quality Bonus' to daily.",
            "logic_py": """
def apply_rule(row, prior_row=None):
    if prior_row:
        actual_daily = Decimal(str(row['daily_amount']))
        prior_daily = Decimal(str(prior_row['daily_amount']))
        variance = actual_daily - prior_daily
        if variance > Decimal('100000'):
            bonus = Decimal('0.01')  # 1%
            return {
                'daily_amount': actual_daily * (Decimal('1') + bonus),
                'wtd_amount': Decimal(str(row['wtd_amount'])),
                'ytd_amount': Decimal(str(row['ytd_amount']))
            }
    return None
""",
            "sql_where": "1=1",  # This rule needs both ACTUAL and PRIOR, handled in application logic
            "node_id": None
        },
        {
            "rule_id": 6,
            "name": "Algo Efficiency",
            "logic_en": "If Strategy == 'ALGO', add a 0.25% 'Efficiency Credit' to ytd_amount.",
            "logic_py": """
def apply_rule(row):
    if row.get('audit_metadata', {}).get('strategy') == 'ALGO':
        ytd = Decimal(str(row['ytd_amount']))
        credit = Decimal('0.0025')  # 0.25%
        return {
            'daily_amount': Decimal(str(row['daily_amount'])),
            'wtd_amount': Decimal(str(row['wtd_amount'])),
            'ytd_amount': ytd * (Decimal('1') + credit)
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'strategy' = 'ALGO')",
            "node_id": None
        },
        {
            "rule_id": 7,
            "name": "UK Regulatory Levy",
            "logic_en": "If Legal Entity == 'UK_LTD', subtract 0.1% for 'Regulatory Fees' from all measures.",
            "logic_py": """
def apply_rule(row):
    if row.get('audit_metadata', {}).get('legal_entity') == 'UK_LTD':
        daily = Decimal(str(row['daily_amount']))
        wtd = Decimal(str(row['wtd_amount']))
        ytd = Decimal(str(row['ytd_amount']))
        levy = Decimal('0.001')  # 0.1%
        return {
            'daily_amount': daily * (Decimal('1') - levy),
            'wtd_amount': wtd * (Decimal('1') - levy),
            'ytd_amount': ytd * (Decimal('1') - levy)
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'legal_entity' = 'UK_LTD')",
            "node_id": None
        },
        {
            "rule_id": 8,
            "name": "Zero-Daily Maintenance",
            "logic_en": "If Daily == 0 and YTD > 1000000, subtract a flat $500 'Maintenance Fee'.",
            "logic_py": """
def apply_rule(row):
    daily = Decimal(str(row['daily_amount']))
    ytd = Decimal(str(row['ytd_amount']))
    if daily == Decimal('0') and ytd > Decimal('1000000'):
        return {
            'daily_amount': Decimal('-500'),
            'wtd_amount': Decimal(str(row['wtd_amount'])) - Decimal('500'),
            'ytd_amount': ytd - Decimal('500')
        }
    return None
""",
            "sql_where": "daily_amount = 0 AND ytd_amount > 1000000",
            "node_id": None
        },
        {
            "rule_id": 9,
            "name": "US Holdings Incentive",
            "logic_en": "If Legal Entity == 'US_HOLDINGS' and Strategy == 'VOL', add a 1.5% multiplier.",
            "logic_py": """
def apply_rule(row):
    metadata = row.get('audit_metadata', {})
    if metadata.get('legal_entity') == 'US_HOLDINGS' and metadata.get('strategy') == 'VOL':
        daily = Decimal(str(row['daily_amount']))
        wtd = Decimal(str(row['wtd_amount']))
        ytd = Decimal(str(row['ytd_amount']))
        multiplier = Decimal('0.015')  # 1.5%
        return {
            'daily_amount': daily * (Decimal('1') + multiplier),
            'wtd_amount': wtd * (Decimal('1') + multiplier),
            'ytd_amount': ytd * (Decimal('1') + multiplier)
        }
    return None
""",
            "sql_where": "EXISTS (SELECT 1 FROM fact_pnl_entries fpe WHERE fpe.id = fact_pnl_entries.id AND fpe.audit_metadata->>'legal_entity' = 'US_HOLDINGS' AND fpe.audit_metadata->>'strategy' = 'VOL')",
            "node_id": None
        },
        {
            "rule_id": 10,
            "name": "Final Rounding",
            "logic_en": "Apply a tiny 0.0001% adjustment to all rows to simulate a 'Rounding Plug'.",
            "logic_py": """
def apply_rule(row):
    daily = Decimal(str(row['daily_amount']))
    wtd = Decimal(str(row['wtd_amount']))
    ytd = Decimal(str(row['ytd_amount']))
    rounding = Decimal('0.000001')  # 0.0001%
    return {
        'daily_amount': daily * (Decimal('1') + rounding),
        'wtd_amount': wtd * (Decimal('1') + rounding),
        'ytd_amount': ytd * (Decimal('1') + rounding)
    }
""",
            "sql_where": "1=1",  # Applies to all rows
            "node_id": None
        }
    ]
    
    created = 0
    updated = 0
    
    for rule_data in rules_data:
        # Get the correct node_id from mapping
        rule_node_id = node_mapping[rule_data['rule_id']]
        
        # Check if rule exists
        existing = session.query(MetadataRule).filter(
            and_(
                MetadataRule.use_case_id == use_case_id,
                MetadataRule.node_id == rule_node_id
            )
        ).first()
        
        # Prepare predicate_json with logic_py
        predicate_json = {
            'logic_py': rule_data['logic_py'],
            'rule_name': rule_data['name'],
            'rule_id': rule_data['rule_id'],
            'measures': ['daily_amount', 'wtd_amount', 'ytd_amount']
        }
        
        if existing:
            # Update existing rule
            existing.logic_en = rule_data['logic_en']
            existing.sql_where = rule_data['sql_where']
            existing.predicate_json = predicate_json
            existing.last_modified_by = 'sterling_step2'
            updated += 1
        else:
            # Create new rule
            new_rule = MetadataRule(
                use_case_id=use_case_id,
                node_id=rule_node_id,
                logic_en=rule_data['logic_en'],
                sql_where=rule_data['sql_where'],
                predicate_json=predicate_json,
                last_modified_by='sterling_step2'
            )
            session.add(new_rule)
            created += 1
    
    session.commit()
    
    return {
        'created': created,
        'updated': updated,
        'total': len(rules_data)
    }


def verify_rules(session: Session, use_case_id: UUID) -> None:
    """Print verification summary of all Sterling rules."""
    rules = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id
    ).all()
    
    # Filter to Sterling rules (those with rule_id in predicate_json)
    sterling_rules = []
    for rule in rules:
        predicate = rule.predicate_json or {}
        if 'rule_id' in predicate and predicate.get('rule_name', '').startswith(('Region', 'Strategy', 'NYC', "Sarah's", 'High-Variance', 'Algo', 'UK', 'Zero-Daily', 'US Holdings', 'Final')):
            sterling_rules.append(rule)
    
    # Sort by rule_id from predicate_json
    sterling_rules.sort(key=lambda r: r.predicate_json.get('rule_id', 0) if r.predicate_json else 0)
    
    print("\n" + "=" * 80)
    print("STERLING RULES VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"{'Rule ID':<10} {'Name':<30} {'Logic EN Snippet':<40}")
    print("-" * 80)
    
    for rule in sterling_rules:
        predicate = rule.predicate_json or {}
        rule_name = predicate.get('rule_name', 'Unknown')
        logic_en_snippet = rule.logic_en[:37] + "..." if len(rule.logic_en) > 40 else rule.logic_en
        
        print(f"{rule.rule_id:<10} {rule_name:<30} {logic_en_snippet:<40}")
    
    print("\n" + "=" * 80)
    print("LOGIC_PY SNIPPETS (First 3 lines of each rule):")
    print("=" * 80)
    
    for rule in sterling_rules:
        predicate = rule.predicate_json or {}
        logic_py = predicate.get('logic_py', '')
        rule_name = predicate.get('rule_name', 'Unknown')
        
        print(f"\n[Rule {rule.rule_id}] {rule_name}:")
        lines = logic_py.strip().split('\n')[:3]
        for line in lines:
            print(f"  {line}")
        if len(logic_py.strip().split('\n')) > 3:
            print("  ...")
    
    print("\n" + "=" * 80)
    print(f"Total Sterling Rules: {len(sterling_rules)}")
    print("=" * 80)


if __name__ == "__main__":
    """
    CLI interface for Sterling Step 2.
    Usage:
        python scripts/sterling_step2_rules.py
    """
    
    print("=" * 80)
    print("Project Sterling - Step 2: Multi-Measure Waterfall Calibration")
    print("=" * 80)
    print("Creating 10 business rules with Python logic...")
    print()
    
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        # Get or create use case
        use_case = get_sterling_use_case(session)
        print(f"Use Case: {use_case.name} (ID: {use_case.use_case_id})")
        print()
        
        # Get or create nodes for rules (one per rule due to unique constraint)
        node_mapping = get_or_create_sterling_nodes(session, use_case)
        print(f"Created/verified {len(node_mapping)} Sterling rule nodes")
        print()
        
        # Create rules
        result = create_sterling_rules(session, use_case.use_case_id, node_mapping)
        
        print("[SUCCESS] Rules created:")
        print(f"   - Created: {result['created']}")
        print(f"   - Updated: {result['updated']}")
        print(f"   - Total: {result['total']}")
        print()
        
        # Verify rules
        verify_rules(session, use_case.use_case_id)
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        session.close()

