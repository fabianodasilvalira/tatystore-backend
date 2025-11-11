"""Add logo_url to companies

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('logo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove coluna logo_url
    op.drop_column('companies', 'logo_url')
