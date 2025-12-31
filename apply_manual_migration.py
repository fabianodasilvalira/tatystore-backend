import sys
import os
from sqlalchemy import create_engine, text

# URL de conexão forçando localhost para rodar fora do docker
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/tatystore"

def apply_migration():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # 1. Adicionar coluna (se não existir)
            try:
                print("Adding unit_cost_price column...")
                connection.execute(text("ALTER TABLE sale_items ADD COLUMN unit_cost_price FLOAT DEFAULT 0.0"))
                print("Column added successfully.")
            except Exception as e:
                # Se falhar, provavelmente já existe. Verificamos a mensagem msg
                if "already exists" in str(e):
                    print("Column unit_cost_price already exists. Skipping.")
                else:
                    print(f"Error adding column: {e}")
                    # Não paramos, pode ser que a coluna já exista.
            
            # 2. Popular dados
            print("Backfilling data from products table...")
            # Atualiza o custo unitário histórico com o custo atual do produto
            # Isso é uma aproximação para vendas passadas
            query = text("""
                UPDATE sale_items 
                SET unit_cost_price = COALESCE(products.cost_price, 0.0)
                FROM products 
                WHERE sale_items.product_id = products.id
            """)
            result = connection.execute(query)
            print(f"Updated {result.rowcount} rows with current product cost.")
            
            connection.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
