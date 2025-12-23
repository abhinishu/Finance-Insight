"""phase_3_1_portability

Revision ID: 135f32906e44
Revises: 089c4ea6fb5e
Create Date: 2025-12-24 00:27:42.880370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '135f32906e44'
down_revision: Union[str, None] = '089c4ea6fb5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create history_snapshots table for Phase 3.1 portability
    op.create_table('history_snapshots',
    sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('use_case_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('snapshot_name', sa.String(length=200), nullable=False),
    sa.Column('snapshot_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.String(length=100), nullable=False),
    sa.Column('rules_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('results_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('version_tag', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['use_case_id'], ['use_cases.use_case_id'], ),
    sa.PrimaryKeyConstraint('snapshot_id')
    )


def downgrade() -> None:
    # Drop history_snapshots table
    op.drop_table('history_snapshots')
