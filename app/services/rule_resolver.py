"""
Rule Resolver Service - Phase 5.1 Unified Hybrid Engine
Converts hierarchy nodes and metadata rules into executable rules.

This service implements the "Rule Resolution Priority" logic:
1. Explicit Custom Rules (Flavor 2/3/4) - Highest Priority
2. Auto-Generated Rules (Flavor 1) - For nodes with rollup_driver
3. NULL Rules - Nodes with no rules get 0.00
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import DimHierarchy, MetadataRule, UseCase
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutableRule:
    """
    Represents an executable rule for a hierarchy node.
    
    Attributes:
        node_id: Hierarchy node ID this rule applies to
        rule_type: Type of rule ('AUTO_SQL', 'FILTER', 'FILTER_ARITHMETIC', 'NODE_ARITHMETIC')
        target_measure: Measure column name to aggregate (e.g., 'daily_pnl', 'pnl_daily')
        filter_col: Column name to filter on (for AUTO_SQL and FILTER rules)
        filter_val: Value to filter for (for AUTO_SQL and FILTER rules)
        sql_where: SQL WHERE clause (for custom FILTER rules)
        rule_expression: Arithmetic expression (for NODE_ARITHMETIC rules)
        rule_dependencies: List of node IDs this rule depends on (for NODE_ARITHMETIC)
        is_virtual: True if this is an auto-generated rule (Flavor 1), False if custom rule
        source_rule_id: Original MetadataRule.rule_id if this came from a custom rule, None for virtual
    """
    node_id: str
    rule_type: str  # 'AUTO_SQL', 'FILTER', 'FILTER_ARITHMETIC', 'NODE_ARITHMETIC'
    target_measure: str  # e.g., 'daily_pnl', 'pnl_daily', 'pnl_commission'
    
    # For AUTO_SQL and FILTER rules
    filter_col: Optional[str] = None
    filter_val: Optional[str] = None
    sql_where: Optional[str] = None
    
    # For NODE_ARITHMETIC rules
    rule_expression: Optional[str] = None
    rule_dependencies: Optional[List[str]] = None
    
    # Metadata
    is_virtual: bool = False  # True for auto-generated rules
    source_rule_id: Optional[int] = None  # MetadataRule.rule_id if custom rule


class RuleResolver:
    """
    Resolves hierarchy nodes into executable rules.
    
    Resolution Priority:
    1. Explicit Custom Rules (from metadata_rules table) - Highest Priority
    2. Auto-Generated Rules (from rollup_driver) - Medium Priority
    3. NULL Rules (no rule) - Lowest Priority (returns None)
    """
    
    def __init__(self, session: Session, use_case_id: UUID):
        """
        Initialize RuleResolver.
        
        Args:
            session: Database session
            use_case_id: Use case UUID
        """
        self.session = session
        self.use_case_id = use_case_id
        self.use_case: Optional[UseCase] = None
        self.measure_mapping: Dict[str, str] = {}
        
        # Load use case and measure mapping
        self._load_use_case()
    
    def _load_use_case(self):
        """Load use case and measure mapping."""
        self.use_case = self.session.query(UseCase).filter(
            UseCase.use_case_id == self.use_case_id
        ).first()
        
        if not self.use_case:
            raise ValueError(f"Use case {self.use_case_id} not found")
        
        # Load measure mapping from use case
        if self.use_case.measure_mapping:
            self.measure_mapping = self.use_case.measure_mapping
        else:
            # Default mapping (for backward compatibility)
            self.measure_mapping = {
                'daily': 'daily_pnl',
                'mtd': 'mtd_pnl',
                'ytd': 'ytd_pnl',
                'pytd': 'pytd_pnl'
            }
            logger.warning(f"Use case {self.use_case_id} has no measure_mapping, using defaults")
    
    def _get_target_measure(self, measure_name: Optional[str] = None) -> str:
        """
        Get target measure column name.
        
        Args:
            measure_name: Optional measure name (e.g., 'daily', 'mtd', 'ytd')
        
        Returns:
            Database column name (e.g., 'daily_pnl', 'pnl_daily')
        """
        if measure_name:
            # If measure_name is provided, try to map it
            if measure_name in self.measure_mapping:
                return self.measure_mapping[measure_name]
            # If it's already a column name, use it directly
            return measure_name
        
        # Default to 'daily' measure
        return self.measure_mapping.get('daily', 'daily_pnl')
    
    def resolve_rules(
        self, 
        hierarchy_nodes: List[DimHierarchy]
    ) -> List[ExecutableRule]:
        """
        Resolve hierarchy nodes into executable rules.
        
        Resolution Logic:
        1. Load all custom rules from metadata_rules for this use case
        2. For each hierarchy node:
           - If custom rule exists: Use it (Flavor 2/3/4)
           - Else if rollup_driver exists: Generate virtual rule (Flavor 1)
           - Else: No rule (will return None for this node)
        
        Args:
            hierarchy_nodes: List of DimHierarchy nodes
        
        Returns:
            List of ExecutableRule objects (one per node with a rule)
        """
        logger.info(f"[RuleResolver] Resolving rules for {len(hierarchy_nodes)} nodes")
        
        # Step 1: Load custom rules from metadata_rules
        custom_rules = self.session.query(MetadataRule).filter(
            MetadataRule.use_case_id == self.use_case_id
        ).all()
        
        custom_rules_dict = {rule.node_id: rule for rule in custom_rules}
        logger.info(f"[RuleResolver] Loaded {len(custom_rules)} custom rules from metadata_rules")
        
        executable_rules = []
        virtual_rules_count = 0
        custom_rules_count = 0
        
        # Step 2: Resolve each node
        for node in hierarchy_nodes:
            # Priority 1: Check for explicit custom rule
            if node.node_id in custom_rules_dict:
                custom_rule = custom_rules_dict[node.node_id]
                executable_rule = self._convert_custom_rule(custom_rule, node)
                if executable_rule:
                    executable_rules.append(executable_rule)
                    custom_rules_count += 1
                    logger.debug(f"[RuleResolver] Node {node.node_id} ({node.node_name}): Using custom rule {custom_rule.rule_id}")
                continue
            
            # Priority 2: Check for rollup_driver (auto-rollup)
            if node.rollup_driver:
                virtual_rule = self._generate_virtual_rule(node)
                if virtual_rule:
                    executable_rules.append(virtual_rule)
                    virtual_rules_count += 1
                    logger.debug(f"[RuleResolver] Node {node.node_id} ({node.node_name}): Generated virtual rule (driver={node.rollup_driver})")
                continue
            
            # Priority 3: No rule (node will have 0.00 value)
            logger.debug(f"[RuleResolver] Node {node.node_id} ({node.node_name}): No rule (will be 0.00 or aggregated from children)")
        
        logger.info(
            f"[RuleResolver] Resolution complete: {len(executable_rules)} rules total "
            f"({custom_rules_count} custom, {virtual_rules_count} virtual)"
        )
        
        return executable_rules
    
    def _convert_custom_rule(
        self, 
        rule: MetadataRule, 
        node: DimHierarchy
    ) -> Optional[ExecutableRule]:
        """
        Convert a MetadataRule (custom rule) into an ExecutableRule.
        
        Args:
            rule: MetadataRule from database
            node: DimHierarchy node this rule applies to
        
        Returns:
            ExecutableRule object
        """
        rule_type = rule.rule_type or 'FILTER'
        target_measure = self._get_target_measure(rule.measure_name)
        
        if rule_type == 'NODE_ARITHMETIC':
            # Flavor 4: Node Math
            return ExecutableRule(
                node_id=node.node_id,
                rule_type='NODE_ARITHMETIC',
                target_measure=target_measure,
                rule_expression=rule.rule_expression,
                rule_dependencies=rule.rule_dependencies or [],
                is_virtual=False,
                source_rule_id=rule.rule_id
            )
        
        elif rule_type == 'FILTER_ARITHMETIC':
            # Flavor 2B: Arithmetic of multiple queries
            # Note: This requires predicate_json parsing (handled separately)
            return ExecutableRule(
                node_id=node.node_id,
                rule_type='FILTER_ARITHMETIC',
                target_measure=target_measure,
                sql_where=rule.sql_where,  # May be None, predicate_json contains the logic
                is_virtual=False,
                source_rule_id=rule.rule_id
            )
        
        elif rule_type == 'FILTER':
            # Flavor 2: Custom SQL
            return ExecutableRule(
                node_id=node.node_id,
                rule_type='FILTER',
                target_measure=target_measure,
                sql_where=rule.sql_where,
                is_virtual=False,
                source_rule_id=rule.rule_id
            )
        
        else:
            logger.warning(f"[RuleResolver] Unknown rule_type '{rule_type}' for rule {rule.rule_id}")
            return None
    
    def _generate_virtual_rule(self, node: DimHierarchy) -> Optional[ExecutableRule]:
        """
        Generate a virtual auto-rollup rule for a node with rollup_driver.
        
        Flavor 1: Auto-Rollup
        - Generates: SELECT SUM({target_measure}) FROM {table} WHERE {rollup_driver} = {filter_val}
        
        Args:
            node: DimHierarchy node with rollup_driver set
        
        Returns:
            ExecutableRule object (virtual rule)
        """
        if not node.rollup_driver:
            return None
        
        # Determine filter value based on rollup_value_source
        if node.rollup_value_source == 'node_name':
            filter_val = node.node_name
        else:
            # Default to node_id
            filter_val = node.node_id
        
        # Get target measure (default to 'daily')
        target_measure = self._get_target_measure('daily')
        
        # Generate virtual rule
        return ExecutableRule(
            node_id=node.node_id,
            rule_type='AUTO_SQL',
            target_measure=target_measure,
            filter_col=node.rollup_driver,
            filter_val=filter_val,
            is_virtual=True,
            source_rule_id=None
        )
    
    def get_rules_by_node(self, executable_rules: List[ExecutableRule]) -> Dict[str, ExecutableRule]:
        """
        Convert list of ExecutableRules into a dictionary keyed by node_id.
        
        Args:
            executable_rules: List of ExecutableRule objects
        
        Returns:
            Dictionary mapping node_id -> ExecutableRule
        """
        return {rule.node_id: rule for rule in executable_rules}


def resolve_rules_for_use_case(
    session: Session,
    use_case_id: UUID,
    hierarchy_nodes: List[DimHierarchy]
) -> List[ExecutableRule]:
    """
    Convenience function to resolve rules for a use case.
    
    Args:
        session: Database session
        use_case_id: Use case UUID
        hierarchy_nodes: List of DimHierarchy nodes
    
    Returns:
        List of ExecutableRule objects
    """
    resolver = RuleResolver(session, use_case_id)
    return resolver.resolve_rules(hierarchy_nodes)

