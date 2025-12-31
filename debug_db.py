import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/tatystore"

def debug_sale_items():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        query = text("""
            SELECT id, sale_id, product_id, quantity, unit_price, total_price, unit_cost_price 
            FROM sale_items 
            ORDER BY id DESC 
            LIMIT 5
        """)
        result = connection.execute(query)
        rows = result.fetchall()
        
        print(f"{'ID':<5} {'SaleID':<8} {'ProdID':<8} {'Qty':<5} {'Price':<10} {'Total':<10} {'UnitCost':<10}")
        print("-" * 70)
        for row in rows:
            print(f"{row.id:<5} {row.sale_id:<8} {row.product_id:<8} {row.quantity:<5} {row.unit_price:<10} {row.total_price:<10} {row.unit_cost_price}")

if __name__ == "__main__":
    debug_sale_items()
