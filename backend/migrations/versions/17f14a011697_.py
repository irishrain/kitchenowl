"""Add used to token model

Revision ID: 17f14a011697
Revises: 22dbfbf4cc33
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17f14a011697'
down_revision = '22dbfbf4cc33'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('token', sa.Column('used', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('token', 'used')