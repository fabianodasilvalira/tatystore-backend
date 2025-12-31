"""
Script alternativo para criar cliente padrão "Venda na Loja"
Usa SQL direto para evitar problemas de importação circular
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import SessionLocal


def create_default_customer_sql():
    """Cria cliente 'Venda na Loja' usando SQL direto"""
    db = SessionLocal()
    
    try:
        # Buscar todas as empresas
        companies_result = db.execute(text("SELECT id, name FROM companies"))
        companies = companies_result.fetchall()
        
        print(f"Encontradas {len(companies)} empresas no sistema.\n")
        
        for company in companies:
            company_id, company_name = company
            
            # Verificar se já existe cliente "Venda na Loja"
            existing = db.execute(
                text("SELECT id FROM customers WHERE company_id = :company_id AND name = :name"),
                {"company_id": company_id, "name": "Venda na Loja"}
            ).fetchone()
            
            if existing:
                print(f"✓ Empresa '{company_name}' já possui cliente 'Venda na Loja' (ID: {existing[0]})")
                continue
            
            # Criar novo cliente
            db.execute(
                text("""
                    INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
                    VALUES (:name, NULL, NULL, NULL, NULL, :company_id, TRUE, NOW(), NOW())
                """),
                {"name": "Venda na Loja", "company_id": company_id}
            )
            db.commit()
            
            # Buscar ID do cliente criado
            new_customer = db.execute(
                text("SELECT id FROM customers WHERE company_id = :company_id AND name = :name"),
                {"company_id": company_id, "name": "Venda na Loja"}
            ).fetchone()
            
            print(f"✓ Cliente 'Venda na Loja' criado para empresa '{company_name}' (ID: {new_customer[0]})")
        
        print("\n✅ Script concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar clientes: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Criando Cliente Padrão 'Venda na Loja' (SQL) ===\n")
    create_default_customer_sql()
