"""add_report_registration_table

Revision ID: b8b0e4b6df61
Revises: 2da3ea852c97
Create Date: 2025-12-20 12:38:36.668351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b8b0e4b6df61'
down_revision: Union[str, None] = '2da3ea852c97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create report_registrations table
    op.create_table(
        'report_registrations',
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_name', sa.String(length=200), nullable=False),
        sa.Column('atlas_structure_id', sa.String(length=200), nullable=False),
        sa.Column('selected_measures', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('selected_dimensions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('owner_id', sa.String(length=100), nullable=False, server_default='default_user'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('report_id')
    )


def downgrade() -> None:
    op.drop_table('report_registrations')
