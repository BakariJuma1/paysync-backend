"""Add business_id to debts with default business

Revision ID: fe58755a7fdc
Revises: db6ae82ebf5e
Create Date: 2025-08-21 11:31:59.855095
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fe58755a7fdc'
down_revision = 'db6ae82ebf5e'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add column as nullable first
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('business_id', sa.Integer(), nullable=True))

    # 2. Insert a default business assigned to the first user
    op.execute("""
        INSERT INTO businesses (id, name, owner_id, created_at)
        SELECT 1, 'Default Business', id, NOW()
        FROM users
        LIMIT 1
        ON CONFLICT (id) DO NOTHING;
    """)

    # 3. Assign all existing debts to this default business
    op.execute("UPDATE debts SET business_id = 1 WHERE business_id IS NULL")

    # 4. Alter column to non-nullable and add foreign key
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.alter_column('business_id', nullable=False)
        batch_op.create_foreign_key(
            'fk_debts_business_id', 'businesses', ['business_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_debts_business_id', type_='foreignkey')
        batch_op.drop_column('business_id')
