"""add_dim_dictionary_and_fact_pnl_entries

Revision ID: 678aa812f5a0
Revises: 089c4ea6fb5e
Create Date: 2025-12-24 02:31:01.601620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '678aa812f5a0'
down_revision: Union[str, None] = '089c4ea6fb5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dim_dictionary table
    op.create_table(
        'dim_dictionary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tech_id', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'tech_id', name='uq_category_tech_id')
    )
    
    # Create fact_pnl_entries table
    op.create_table(
        'fact_pnl_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pnl_date', sa.Date(), nullable=False),
        sa.Column('category_code', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('scenario', sa.String(length=20), nullable=False),
        sa.Column('audit_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['use_case_id'], ['use_cases.use_case_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_dim_dictionary_category', 'dim_dictionary', ['category'])
    op.create_index('ix_dim_dictionary_tech_id', 'dim_dictionary', ['tech_id'])
    op.create_index('ix_fact_pnl_entries_use_case_id', 'fact_pnl_entries', ['use_case_id'])
    op.create_index('ix_fact_pnl_entries_pnl_date', 'fact_pnl_entries', ['pnl_date'])
    op.create_index('ix_fact_pnl_entries_scenario', 'fact_pnl_entries', ['scenario'])
    
    # Update existing foreign keys to use ON DELETE CASCADE
    # Drop and recreate foreign key constraints with CASCADE
    op.drop_constraint('use_case_runs_use_case_id_fkey', 'use_case_runs', type_='foreignkey')
    op.create_foreign_key(
        'use_case_runs_use_case_id_fkey',
        'use_case_runs', 'use_cases',
        ['use_case_id'], ['use_case_id'],
        ondelete='CASCADE'
    )
    
    op.drop_constraint('metadata_rules_use_case_id_fkey', 'metadata_rules', type_='foreignkey')
    op.create_foreign_key(
        'metadata_rules_use_case_id_fkey',
        'metadata_rules', 'use_cases',
        ['use_case_id'], ['use_case_id'],
        ondelete='CASCADE'
    )
    
    op.drop_constraint('fact_calculated_results_run_id_fkey', 'fact_calculated_results', type_='foreignkey')
    op.create_foreign_key(
        'fact_calculated_results_run_id_fkey',
        'fact_calculated_results', 'use_case_runs',
        ['run_id'], ['run_id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_fact_pnl_entries_scenario', table_name='fact_pnl_entries')
    op.drop_index('ix_fact_pnl_entries_pnl_date', table_name='fact_pnl_entries')
    op.drop_index('ix_fact_pnl_entries_use_case_id', table_name='fact_pnl_entries')
    op.drop_index('ix_dim_dictionary_tech_id', table_name='dim_dictionary')
    op.drop_index('ix_dim_dictionary_category', table_name='dim_dictionary')
    
    # Drop tables
    op.drop_table('fact_pnl_entries')
    op.drop_table('dim_dictionary')
    
    # Revert foreign keys to original (without CASCADE)
    op.drop_constraint('fact_calculated_results_run_id_fkey', 'fact_calculated_results', type_='foreignkey')
    op.create_foreign_key(
        'fact_calculated_results_run_id_fkey',
        'fact_calculated_results', 'use_case_runs',
        ['run_id'], ['run_id']
    )
    
    op.drop_constraint('metadata_rules_use_case_id_fkey', 'metadata_rules', type_='foreignkey')
    op.create_foreign_key(
        'metadata_rules_use_case_id_fkey',
        'metadata_rules', 'use_cases',
        ['use_case_id'], ['use_case_id']
    )
    
    op.drop_constraint('use_case_runs_use_case_id_fkey', 'use_case_runs', type_='foreignkey')
    op.create_foreign_key(
        'use_case_runs_use_case_id_fkey',
        'use_case_runs', 'use_cases',
        ['use_case_id'], ['use_case_id']
    )
