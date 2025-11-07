from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_model_enhancements'
down_revision = '0001_init'
branch_labels = None
depends_on = None

def upgrade():
    # company
    op.add_column('companies', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))
    op.add_column('companies', sa.Column('admin_email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('cobranca_email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('config_json', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('logo_url', sa.String(length=512), nullable=True))

    # user
    op.add_column('users', sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # product
    op.add_column('products', sa.Column('cost_price', sa.Numeric(10,2), nullable=True, server_default='0'))

    # customer
    op.add_column('customers', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('customers', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('customers', sa.Column('obs', sa.Text(), nullable=True))

    # sale
    op.add_column('sales', sa.Column('discount_amount', sa.Numeric(10,2), nullable=False, server_default='0'))

    # installment
    op.add_column('installments', sa.Column('payment_date', sa.Date(), nullable=True))

def downgrade():
    op.drop_column('installments', 'payment_date')
    op.drop_column('sales', 'discount_amount')
    op.drop_column('customers', 'obs')
    op.drop_column('customers', 'birth_date')
    op.drop_column('customers', 'email')
    op.drop_column('products', 'cost_price')
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'last_login_at')
    op.drop_column('companies', 'logo_url')
    op.drop_column('companies', 'config_json')
    op.drop_column('companies', 'cobranca_email')
    op.drop_column('companies', 'admin_email')
    op.drop_column('companies', 'status')

