"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)

    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create role_permissions junction table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('cnpj', sa.String(length=14), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_companies_slug'), 'companies', ['slug'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create customers table
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('cpf', sa.String(length=11), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_cpf'), 'customers', ['cpf'], unique=False)

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('cost_price', sa.Float(), nullable=False),
        sa.Column('sale_price', sa.Float(), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=True),
        sa.Column('min_stock', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_barcode'), 'products', ['barcode'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)

    # Create sales table
    op.create_table('sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payment_type', sa.Enum('cash', 'credit', 'pix', name='paymenttype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'cancelled', name='salestatus'), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('installments_count', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sale_items table
    op.create_table('sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create installments table
    op.create_table('installments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'paid', 'overdue', 'cancelled', name='installmentstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('login_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_attempts_email'), 'login_attempts', ['email'], unique=False)

    op.create_table('audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('captcha_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('answer', sa.String(length=10), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    op.create_table('password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_email', sa.String(length=200), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('password_reset_tokens')
    op.drop_table('captcha_challenges')
    op.drop_table('audit_logs')
    op.drop_table('login_attempts')
    op.drop_table('installments')
    op.drop_table('sale_items')
    op.drop_table('sales')
    op.drop_table('products')
    op.drop_table('customers')
    op.drop_table('users')
    op.drop_index(op.f('ix_companies_slug'), table_name='companies')
    op.drop_table('companies')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_table('permissions')
