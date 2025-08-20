"""empty message

Revision ID: db6ae82ebf5e
Revises: 
Create Date: 2025-08-20 10:15:11.720595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db6ae82ebf5e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add with a default so old rows don’t break
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'category',
            sa.String(),
            nullable=False,
            server_default="Uncategorized"   # ✅ important
        ))


def downgrade():
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.drop_column('category')
