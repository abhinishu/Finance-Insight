"""Initial migration: create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    use_case_status_enum = postgresql.ENUM('DRAFT', 'ACTIVE', 'ARCHIVED', name='usecasestatus', create_type=True)
    use_case_status_enum.create(op.get_bind(), checkfirst=True)
    
    run_status_enum = postgresql.ENUM('IN_PROGRESS', 'COMPLETED', 'FAILED', name='runstatus', create_type=True)
    run_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create use_cases table
    op.create_table(
        'use_cases',
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('atlas_structure_id', sa.String(), nullable=False),
        sa.Column('status', use_case_status_enum, nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('use_case_id')
    )
    
    # Create use_case_runs table
    op.create_table(
        'use_case_runs',
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_tag', sa.String(), nullable=False),
        sa.Column('run_timestamp', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('parameters_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', run_status_enum, nullable=False, server_default='IN_PROGRESS'),
        sa.Column('triggered_by', sa.String(), nullable=False),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['use_case_id'], ['use_cases.use_case_id'], ),
        sa.PrimaryKeyConstraint('run_id')
    )
    
    # Create dim_hierarchy table
    op.create_table(
        'dim_hierarchy',
        sa.Column('node_id', sa.String(length=50), nullable=False),
        sa.Column('parent_node_id', sa.String(length=50), nullable=True),
        sa.Column('node_name', sa.String(), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('is_leaf', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('atlas_source', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['parent_node_id'], ['dim_hierarchy.node_id'], ),
        sa.PrimaryKeyConstraint('node_id')
    )
    
    # Create metadata_rules table
    op.create_table(
        'metadata_rules',
        sa.Column('rule_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(length=50), nullable=False),
        sa.Column('predicate_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sql_where', sa.Text(), nullable=False),
        sa.Column('logic_en', sa.Text(), nullable=True),
        sa.Column('last_modified_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_modified_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['dim_hierarchy.node_id'], ),
        sa.ForeignKeyConstraint(['use_case_id'], ['use_cases.use_case_id'], ),
        sa.PrimaryKeyConstraint('rule_id'),
        sa.UniqueConstraint('use_case_id', 'node_id', name='uq_use_case_node')
    )
    
    # Create fact_pnl_gold table
    op.create_table(
        'fact_pnl_gold',
        sa.Column('fact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=False),
        sa.Column('cc_id', sa.String(length=50), nullable=False),
        sa.Column('book_id', sa.String(length=50), nullable=False),
        sa.Column('strategy_id', sa.String(length=50), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('daily_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('mtd_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('ytd_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('pytd_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('fact_id')
    )
    
    # Create fact_calculated_results table
    op.create_table(
        'fact_calculated_results',
        sa.Column('result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(length=50), nullable=False),
        sa.Column('measure_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('plug_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_reconciled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['dim_hierarchy.node_id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['use_case_runs.run_id'], ),
        sa.PrimaryKeyConstraint('result_id')
    )
    
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
    op.create_index('ix_use_case_runs_use_case_id', 'use_case_runs', ['use_case_id'])
    op.create_index('ix_metadata_rules_use_case_id', 'metadata_rules', ['use_case_id'])
    op.create_index('ix_metadata_rules_node_id', 'metadata_rules', ['node_id'])
    op.create_index('ix_fact_pnl_gold_cc_id', 'fact_pnl_gold', ['cc_id'])
    op.create_index('ix_fact_calculated_results_run_id', 'fact_calculated_results', ['run_id'])
    op.create_index('ix_fact_calculated_results_node_id', 'fact_calculated_results', ['node_id'])
    op.create_index('ix_hierarchy_bridge_parent', 'hierarchy_bridge', ['parent_node_id'])
    op.create_index('ix_hierarchy_bridge_leaf', 'hierarchy_bridge', ['leaf_node_id'])
    op.create_index('ix_hierarchy_bridge_structure', 'hierarchy_bridge', ['structure_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_hierarchy_bridge_structure', table_name='hierarchy_bridge')
    op.drop_index('ix_hierarchy_bridge_leaf', table_name='hierarchy_bridge')
    op.drop_index('ix_hierarchy_bridge_parent', table_name='hierarchy_bridge')
    op.drop_index('ix_fact_calculated_results_node_id', table_name='fact_calculated_results')
    op.drop_index('ix_fact_calculated_results_run_id', table_name='fact_calculated_results')
    op.drop_index('ix_fact_pnl_gold_cc_id', table_name='fact_pnl_gold')
    op.drop_index('ix_metadata_rules_node_id', table_name='metadata_rules')
    op.drop_index('ix_metadata_rules_use_case_id', table_name='metadata_rules')
    op.drop_index('ix_use_case_runs_use_case_id', table_name='use_case_runs')
    
    # Drop tables in reverse order
    op.drop_table('hierarchy_bridge')
    op.drop_table('fact_calculated_results')
    op.drop_table('fact_pnl_gold')
    op.drop_table('metadata_rules')
    op.drop_table('dim_hierarchy')
    op.drop_table('use_case_runs')
    op.drop_table('use_cases')
    
    # Drop enum types
    sa.Enum(name='runstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='usecasestatus').drop(op.get_bind(), checkfirst=True)

