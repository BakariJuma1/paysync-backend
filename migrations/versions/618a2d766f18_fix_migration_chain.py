from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '618a2d766f18'
down_revision = 'c3044d506731'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: add column as nullable
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(), nullable=True))

    # Step 2: set default value for existing rows
    op.execute("UPDATE debts SET category = 'Uncategorized' WHERE category IS NULL")

    # Step 3: enforce NOT NULL
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.alter_column('category', nullable=False)

        # finally drop balance column
        batch_op.drop_column('balance')


def downgrade():
    with op.batch_alter_table('debts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('balance', sa.Numeric(), nullable=True))
        batch_op.drop_column('category')
