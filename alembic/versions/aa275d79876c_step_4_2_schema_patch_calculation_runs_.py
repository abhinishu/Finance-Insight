"""step_4_2_schema_patch_calculation_runs_and_explicit_measures

Revision ID: aa275d79876c
Revises: 678aa812f5a0
Create Date: 2025-12-24 02:43:50.986369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'aa275d79876c'
down_revision: Union[str, None] = '678aa812f5a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add explicit measure columns to fact_pnl_entries
    # Keep 'amount' column for backward compatibility, add daily/wtd/ytd
    op.add_column('fact_pnl_entries', sa.Column('daily_amount', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('fact_pnl_entries', sa.Column('wtd_amount', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('fact_pnl_entries', sa.Column('ytd_amount', sa.Numeric(precision=18, scale=2), nullable=True))
    
    # For existing rows, populate from 'amount' (assuming it represents daily)
    # In production, you'd want to backfill from source data
    op.execute("""
        UPDATE fact_pnl_entries 
        SET daily_amount = amount,
            wtd_amount = amount,
            ytd_amount = amount
        WHERE daily_amount IS NULL
    """)
    
    # Make columns NOT NULL after backfill
    op.alter_column('fact_pnl_entries', 'daily_amount', nullable=False)
    op.alter_column('fact_pnl_entries', 'wtd_amount', nullable=False)
    op.alter_column('fact_pnl_entries', 'ytd_amount', nullable=False)
    
    # Step 2: Create calculation_runs table (Header for temporal versioning)
    op.create_table(
        'calculation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pnl_date', sa.Date(), nullable=False),
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_name', sa.String(length=200), nullable=False),
        sa.Column('executed_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('triggered_by', sa.String(length=100), nullable=False),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['use_case_id'], ['use_cases.use_case_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for calculation_runs
    op.create_index('ix_calculation_runs_pnl_date', 'calculation_runs', ['pnl_date'])
    op.create_index('ix_calculation_runs_use_case_id', 'calculation_runs', ['use_case_id'])
    op.create_index('ix_calculation_runs_date_use_case', 'calculation_runs', ['pnl_date', 'use_case_id'])
    
    # Step 3: Add calculation_run_id to fact_calculated_results (reporting_results)
    # Keep run_id for backward compatibility during transition
    op.add_column('fact_calculated_results', sa.Column('calculation_run_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fact_calculated_results_calculation_run_id_fkey',
        'fact_calculated_results', 'calculation_runs',
        ['calculation_run_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_fact_calculated_results_calc_run_id', 'fact_calculated_results', ['calculation_run_id'])


def downgrade() -> None:
    # Remove calculation_run_id from fact_calculated_results
    op.drop_index('ix_fact_calculated_results_calc_run_id', table_name='fact_calculated_results')
    op.drop_constraint('fact_calculated_results_calculation_run_id_fkey', 'fact_calculated_results', type_='foreignkey')
    op.drop_column('fact_calculated_results', 'calculation_run_id')
    
    # Drop calculation_runs table
    op.drop_index('ix_calculation_runs_date_use_case', table_name='calculation_runs')
    op.drop_index('ix_calculation_runs_use_case_id', table_name='calculation_runs')
    op.drop_index('ix_calculation_runs_pnl_date', table_name='calculation_runs')
    op.drop_table('calculation_runs')
    
    # Remove explicit measure columns from fact_pnl_entries
    op.drop_column('fact_pnl_entries', 'ytd_amount')
    op.drop_column('fact_pnl_entries', 'wtd_amount')
    op.drop_column('fact_pnl_entries', 'daily_amount')
