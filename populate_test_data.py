"""
Script para popular banco de dados com dados de teste usando SQL direto
Executa: python populate_test_data.py
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def populate_test_data():
    """Popula banco de dados com dados de teste"""
    
    # Conectar ao banco (credenciais do docker-compose)
    DATABASE_URL = "postgresql://postgres:postgres@db:5432/tatystore"
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🔄 Populando dados de teste...")
        
        # 1. Verificar empresa
        cur.execute("SELECT id, name FROM companies LIMIT 1")
        company = cur.fetchone()
        if not company:
            print("❌ Nenhuma empresa encontrada. Execute o seed primeiro.")
            return
        
        company_id = company[0]
        print(f"✅ Empresa encontrada: {company[1]} (ID: {company_id})")
        
        # 2. Criar cliente de teste
        cur.execute("""
            INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
            VALUES ('Cliente Teste', 'cliente.teste@example.com', '11999999999', '12345678901', 'Rua Teste, 123', %s, true, NOW(), NOW())
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (company_id,))
        
        result = cur.fetchone()
        if result:
            customer_id = result[0]
            print(f"✅ Cliente de teste criado (ID: {customer_id})")
        else:
            # Cliente já existe, buscar ID
            cur.execute("SELECT id FROM customers WHERE email = 'cliente.teste@example.com' AND company_id = %s", (company_id,))
            customer_id = cur.fetchone()[0]
            print(f"✅ Cliente de teste já existe (ID: {customer_id})")
        
        # 3. Criar categoria de teste
        cur.execute("""
            INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
            VALUES ('Categoria Teste', 'Categoria para testes', %s, true, NOW(), NOW())
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (company_id,))
        
        result = cur.fetchone()
        if result:
            category_id = result[0]
            print(f"✅ Categoria de teste criada (ID: {category_id})")
        else:
            # Categoria já existe, buscar ID
            cur.execute("SELECT id FROM categories WHERE name = 'Categoria Teste' AND company_id = %s", (company_id,))
            category_id = cur.fetchone()[0]
            print(f"✅ Categoria de teste já existe (ID: {category_id})")
        
        # 4. Criar produtos de teste
        products = [
            ("Produto Teste 1", "TEST001", "7890000000001", 10.00, 20.00, 100, 10),
            ("Produto Teste 2", "TEST002", "7890000000002", 25.00, 50.00, 50, 5),
            ("Produto Teste 3 (Estoque Baixo)", "TEST003", "7890000000003", 5.00, 10.00, 5, 10),
        ]
        
        for product in products:
            name, sku, barcode, cost, sale, stock, min_stock = product
            
            # Verificar se produto já existe
            cur.execute("SELECT id FROM products WHERE sku = %s AND company_id = %s", (sku, company_id))
            existing = cur.fetchone()
            
            if existing:
                print(f"✅ Produto '{name}' já existe (ID: {existing[0]})")
            else:
                cur.execute("""
                    INSERT INTO products (name, sku, barcode, cost_price, sale_price, stock_quantity, min_stock, 
                                         category_id, company_id, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
                    RETURNING id
                """, (name, sku, barcode, cost, sale, stock, min_stock, category_id, company_id))
                
                result = cur.fetchone()
                print(f"✅ Produto '{name}' criado (ID: {result[0]}, Estoque: {stock})")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ DADOS DE TESTE POPULADOS COM SUCESSO!")
        print("="*60)
        print(f"\n📊 Resumo:")
        print(f"  - Empresa ID: {company_id}")
        print(f"  - Cliente ID: {customer_id}")
        print(f"  - Categoria ID: {category_id}")
        print(f"  - Produtos: 3 criados/verificados")
        print(f"\n🧪 Agora você pode executar os testes!")
        print(f"  powershell -ExecutionPolicy Bypass -File C:\\Users\\User\\.gemini\\antigravity\\brain\\79a1903b-a907-4abe-844e-cfd3728d29b2\\test_correcoes.ps1")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro ao popular dados: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    populate_test_data()
