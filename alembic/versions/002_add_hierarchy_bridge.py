"""Add hierarchy_bridge table

Revision ID: 002_add_bridge
Revises: 001_initial
Create Date: 2024-12-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_bridge'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create hierarchy_bridge table
    op.create_table(
        'hierarchy_bridge',
        sa.Column('bridge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_node_id', sa.String(length=50), nullable=False),
        sa.Column('leaf_node_id', sa.String(length=50), nullable=False),
        sa.Column('structure_id', sa.String(), nullable=False),
        sa.Column('path_length', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['leaf_node_id'], ['dim_hierarchy.node_id'], ),
        sa.ForeignKeyConstraint(['parent_node_id'], ['dim_hierarchy.node_id'], ),
        sa.PrimaryKeyConstraint('bridge_id')
    )
    
    # Create indexes for performance
    op.create_index('ix_hierarchy_bridge_parent', 'hierarchy_bridge', ['parent_node_id'])
    op.create_index('ix_hierarchy_bridge_leaf', 'hierarchy_bridge', ['leaf_node_id'])
    op.create_index('ix_hierarchy_bridge_structure', 'hierarchy_bridge', ['structure_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_hierarchy_bridge_structure', table_name='hierarchy_bridge')
    op.drop_index('ix_hierarchy_bridge_leaf', table_name='hierarchy_bridge')
    op.drop_index('ix_hierarchy_bridge_parent', table_name='hierarchy_bridge')
    
    # Drop table
    op.drop_table('hierarchy_bridge')

