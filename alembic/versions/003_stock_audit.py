"""add stock_movements table and stock constraints

Revision ID: 003_stock_audit
Revises: 002_add_product_brand_and_image
Create Date: 2025-12-31 10:09:00.000000

ATENÇÃO: Esta migração adiciona:
1. Tabela stock_movements para auditoria de estoque
2. Constraints de estoque não-negativo em products
3. Correção de is_on_sale NOT NULL em products

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_stock_audit'
down_revision = '002_add_product_brand_and_image'
branch_labels = None
depends_on = None


def upgrade():
    """
    Aplica as mudanças no banco de dados.
    SEGURO para produção - corrige dados antes de aplicar constraints.
    """
    
    # 1. Criar enum para movement_type
    movement_type_enum = postgresql.ENUM('sale', 'cancel', 'adjustment', 'return', name='movementtype')
    movement_type_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Criar tabela stock_movements
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', movement_type_enum, nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('previous_stock', sa.Integer(), nullable=False),
        sa.Column('new_stock', sa.Integer(), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 3. Criar índices para performance
    op.create_index('ix_stock_movements_id', 'stock_movements', ['id'])
    op.create_index('ix_stock_movements_product_id', 'stock_movements', ['product_id'])
    op.create_index('ix_stock_movements_company_id', 'stock_movements', ['company_id'])
    op.create_index('ix_stock_movements_created_at', 'stock_movements', ['created_at'])
    
    # 4. CORRIGIR dados antes de aplicar constraints
    # Corrigir produtos com estoque negativo
    op.execute("""
        UPDATE products 
        SET stock_quantity = 0 
        WHERE stock_quantity < 0;
    """)
    
    op.execute("""
        UPDATE products 
        SET min_stock = 0 
        WHERE min_stock < 0;
    """)
    
    # 5. Adicionar constraints de estoque (apenas se não existirem)
    # Usar try/except via SQL para evitar erro se já existir
    op.execute("""
        DO $$ 
        BEGIN
            ALTER TABLE products 
            ADD CONSTRAINT check_stock_non_negative 
            CHECK (stock_quantity >= 0);
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'Constraint check_stock_non_negative já existe';
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            ALTER TABLE products 
            ADD CONSTRAINT check_min_stock_non_negative 
            CHECK (min_stock >= 0);
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'Constraint check_min_stock_non_negative já existe';
        END $$;
    """)
    
    # 6. Corrigir is_on_sale NULL e tornar NOT NULL
    op.execute("""
        UPDATE products 
        SET is_on_sale = false 
        WHERE is_on_sale IS NULL;
    """)
    
    op.alter_column(
        'products', 
        'is_on_sale',
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text('false')
    )


def downgrade():
    """
    Reverte as mudanças (rollback).
    Use com CUIDADO em produção!
    """
    
    # Reverter is_on_sale para nullable
    op.alter_column(
        'products', 
        'is_on_sale',
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None
    )
    
    # Remover constraints de products (se existirem)
    op.execute("""
        DO $$ 
        BEGIN
            ALTER TABLE products 
            DROP CONSTRAINT IF EXISTS check_min_stock_non_negative;
        EXCEPTION
            WHEN undefined_object THEN 
                RAISE NOTICE 'Constraint check_min_stock_non_negative não existe';
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            ALTER TABLE products 
            DROP CONSTRAINT IF EXISTS check_stock_non_negative;
        EXCEPTION
            WHEN undefined_object THEN 
                RAISE NOTICE 'Constraint check_stock_non_negative não existe';
        END $$;
    """)
    
    # Remover índices
    op.drop_index('ix_stock_movements_created_at', table_name='stock_movements')
    op.drop_index('ix_stock_movements_company_id', table_name='stock_movements')
    op.drop_index('ix_stock_movements_product_id', table_name='stock_movements')
    op.drop_index('ix_stock_movements_id', table_name='stock_movements')
    
    # Remover tabela
    op.drop_table('stock_movements')
    
    # Remover enum
    movement_type_enum = postgresql.ENUM('sale', 'cancel', 'adjustment', 'return', name='movementtype')
    movement_type_enum.drop(op.get_bind(), checkfirst=True)
