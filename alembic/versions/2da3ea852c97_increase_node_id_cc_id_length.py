"""increase_node_id_cc_id_length

Revision ID: 2da3ea852c97
Revises: 002_add_bridge
Create Date: 2025-12-20 00:04:16.302155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2da3ea852c97'
down_revision: Union[str, None] = '002_add_bridge'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Increase node_id and cc_id column sizes to support realistic finance domain naming
    # Cost center IDs like "CC_AMER_CASH_EQUITIES_HIGH_TOUCH_AMER_CASH_HIGH_TOUCH_001" need more than 50 chars
    
    # Increase dim_hierarchy.node_id and parent_node_id
    op.alter_column('dim_hierarchy', 'node_id', type_=sa.String(length=200))
    op.alter_column('dim_hierarchy', 'parent_node_id', type_=sa.String(length=200))
    
    # Increase fact_pnl_gold.cc_id
    op.alter_column('fact_pnl_gold', 'cc_id', type_=sa.String(length=200))
    
    # Increase hierarchy_bridge node_id columns
    op.alter_column('hierarchy_bridge', 'parent_node_id', type_=sa.String(length=200))
    op.alter_column('hierarchy_bridge', 'leaf_node_id', type_=sa.String(length=200))
    
    # Increase metadata_rules.node_id
    op.alter_column('metadata_rules', 'node_id', type_=sa.String(length=200))
    
    # Increase fact_calculated_results.node_id
    op.alter_column('fact_calculated_results', 'node_id', type_=sa.String(length=200))


def downgrade() -> None:
    # Revert to original VARCHAR(50) - WARNING: May fail if data exists with longer IDs
    op.alter_column('dim_hierarchy', 'node_id', type_=sa.String(length=50))
    op.alter_column('dim_hierarchy', 'parent_node_id', type_=sa.String(length=50))
    op.alter_column('fact_pnl_gold', 'cc_id', type_=sa.String(length=50))
    op.alter_column('hierarchy_bridge', 'parent_node_id', type_=sa.String(length=50))
    op.alter_column('hierarchy_bridge', 'leaf_node_id', type_=sa.String(length=50))
    op.alter_column('metadata_rules', 'node_id', type_=sa.String(length=50))
    op.alter_column('fact_calculated_results', 'node_id', type_=sa.String(length=50))
