"""add_scopes_to_report_registration

Revision ID: 089c4ea6fb5e
Revises: b8b0e4b6df61
Create Date: 2025-12-20 13:10:43.314787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '089c4ea6fb5e'
down_revision: Union[str, None] = 'b8b0e4b6df61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add measure_scopes and dimension_scopes columns to report_registrations
    op.add_column('report_registrations', sa.Column('measure_scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('report_registrations', sa.Column('dimension_scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('report_registrations', 'dimension_scopes')
    op.drop_column('report_registrations', 'measure_scopes')
