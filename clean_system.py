
from app.core.database import SessionLocal
from sqlalchemy import text
from app.core.datetime_utils import get_now_fortaleza_naive

def clean_system():
    print("🧹 Iniciando limpeza do sistema (MODO SQL PURO)...")
    db = SessionLocal()
    try:
        # Obter empresa principal via SQL
        result = db.execute(text("SELECT id, name FROM companies WHERE name = 'Taty Perfumaria'"))
        taty = result.fetchone()
        
        if not taty:
            print("⚠️ Empresa 'Taty Perfumaria' não encontrada. Abortando limpeza.")
            return

        print(f"🏢 Empresa encontrada: {taty.name} (ID: {taty.id})")
        taty_id = taty.id

        # Limpeza via SQL
        print("🗑️  Excluindo Parcelas...")
        db.execute(text("DELETE FROM installments WHERE company_id = :cid"), {"cid": taty_id})
        
        print("🗑️  Excluindo Itens de Venda...")
        db.execute(text("""
            DELETE FROM sale_items 
            WHERE sale_id IN (SELECT id FROM sales WHERE company_id = :cid)
        """), {"cid": taty_id})
        
        print("🗑️  Excluindo Vendas...")
        db.execute(text("DELETE FROM sales WHERE company_id = :cid"), {"cid": taty_id})
        
        print("🗑️  Excluindo Produtos...")
        db.execute(text("DELETE FROM products WHERE company_id = :cid"), {"cid": taty_id})
        
        print("🗑️  Excluindo Clientes...")
        db.execute(text("DELETE FROM customers WHERE company_id = :cid"), {"cid": taty_id})

        print("✨ Sistema limpo (Tabelas limpas)!")

        # 4. Atualizar Categorias via SQL
        print("📂 Sincronizando Categorias...")
        categories_data = [
            ("Perfumes Masculino", "Fragrâncias masculinas (Boticário, Natura, etc)"),
            ("Perfumes Feminino", "Fragrâncias femininas (Boticário, Natura, etc)"),
            ("Maquiagem", "Produtos de maquiagem para rosto, olhos e lábios"),
            ("Cuidados com a Pele", "Cremes, loções e produtos para cuidados faciais e corporais"),
            ("Cabelos", "Shampoos, condicionadores e tratamentos capilares"),
            ("Kits e Presentes", "Kits promocionais e presentes especiais"),
        ]

        current_time = get_now_fortaleza_naive()
        
        for name, description in categories_data:
            # Verifica se existe
            res = db.execute(text("SELECT id FROM categories WHERE name = :name AND company_id = :cid"), 
                             {"name": name, "cid": taty_id})
            existing = res.fetchone()
            
            if not existing:
                print(f"   [+] Criando categoria: {name}")
                db.execute(text("""
                    INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
                    VALUES (:name, :desc, :cid, true, :now, :now)
                """), {
                    "name": name, 
                    "desc": description, 
                    "cid": taty_id, 
                    "now": current_time
                })
            else:
                print(f"   [OK] Categoria já existe: {name}")
        
        # Limpar categorias obsoletas
        allowed_names = list(set([c[0] for c in categories_data])) # list for safety
        
        # DELETE com NOT IN precisa de cuidado com lista vazia, mas aqui temos valores.
        # SQLAlchemy text bindparam com lista:
        # Precisamos passar tuple para o IN
        
        # Vamos construir a string SQL dinâmica para o IN clause pq text() as vezes chato com listas
        names_str = "', '".join(allowed_names)
        query = f"DELETE FROM categories WHERE company_id = :cid AND name NOT IN ('{names_str}')"
        
        db.execute(text(query), {"cid": taty_id})
        print("   [-] Categorias obsoletas removidas.")

        db.commit()
        print("✅ Categorias Sincronizadas!")
        print("🚀 Sistema pronto para importação.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao limpar sistema: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clean_system()
