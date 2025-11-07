from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_init_all'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    # users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # roles, permissions, associations
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255)),
    )
    op.create_table('role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True),
    )
    op.create_table('user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    )

    # customers
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20)),
        sa.Column('address', sa.Text()),
        sa.Column('cpf', sa.String(length=14), unique=True),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_customers_status', 'customers', ['status'])
    op.create_index('ix_customers_name', 'customers', ['name'])
    op.create_index('ix_customers_cpf', 'customers', ['cpf'])

    # products
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=100)),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Numeric(10,2)),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('photo_url', sa.Text()),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_products_status', 'products', ['status'])
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_brand', 'products', ['brand'])

    # sales
    op.create_table('sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id')),
        sa.Column('total_amount', sa.Numeric(10,2), nullable=False),
        sa.Column('payment_method', sa.String(length=10), nullable=False),
        sa.Column('sale_date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('first_due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=15), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_sales_sale_date', 'sales', ['sale_date'])
    op.create_index('ix_sales_status', 'sales', ['status'])
    op.create_index('ix_sales_payment_method', 'sales', ['payment_method'])
    op.create_index('ix_sales_customer_id', 'sales', ['customer_id'])

    # sale_items
    op.create_table('sale_items',
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales.id'), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), primary_key=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10,2), nullable=False),
    )

    # installments
    op.create_table('installments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sales.id')),
        sa.Column('amount', sa.Numeric(10,2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_installments_status', 'installments', ['status'])
    op.create_index('ix_installments_due_date', 'installments', ['due_date'])
    op.create_index('ix_installments_sale_id', 'installments', ['sale_id'])

    # security & audit
    op.create_table('password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('token', postgresql.UUID(as_uuid=True), unique=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_table('login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=12), nullable=False),
        sa.Column('ip', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_table('captcha_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(length=64), unique=True, index=True),
        sa.Column('answer', sa.String(length=10)),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )

    # Materialized View for reports
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS sales_summary_mv AS
        SELECT date_trunc('day', sale_date) AS day,
               COUNT(*) AS total_sales,
               SUM(total_amount) AS total_revenue
        FROM sales
        WHERE status = 'completed'
        GROUP BY day;
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_sales_summary_mv_day ON sales_summary_mv (day);")

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS sales_summary_mv;")
    op.drop_table('captcha_challenges')
    op.drop_table('audit_logs')
    op.drop_table('login_attempts')
    op.drop_table('password_reset_tokens')
    op.drop_index('ix_installments_sale_id', table_name='installments')
    op.drop_index('ix_installments_due_date', table_name='installments')
    op.drop_index('ix_installments_status', table_name='installments')
    op.drop_table('installments')
    op.drop_table('sale_items')
    op.drop_index('ix_sales_customer_id', table_name='sales')
    op.drop_index('ix_sales_payment_method', table_name='sales')
    op.drop_index('ix_sales_status', table_name='sales')
    op.drop_index('ix_sales_sale_date', table_name='sales')
    op.drop_table('sales')
    op.drop_index('ix_products_brand', table_name='products')
    op.drop_index('ix_products_name', table_name='products')
    op.drop_index('ix_products_status', table_name='products')
    op.drop_table('products')
    op.drop_index('ix_customers_cpf', table_name='customers')
    op.drop_index('ix_customers_name', table_name='customers')
    op.drop_index('ix_customers_status', table_name='customers')
    op.drop_table('customers')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
