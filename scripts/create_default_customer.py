"""
Script para criar cliente padrão "Venda na Loja" para todas as empresas
Este cliente será usado para vendas rápidas no balcão
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.customer import Customer


def create_default_customer():
    """Cria cliente 'Venda na Loja' para todas as empresas que ainda não o possuem"""
    db: Session = SessionLocal()
    
    try:
        # Buscar todas as empresas
        companies = db.query(Company).all()
        
        print(f"Encontradas {len(companies)} empresas no sistema.")
        
        for company in companies:
            # Verificar se já existe um cliente "Venda na Loja" para esta empresa
            existing_customer = db.query(Customer).filter(
                Customer.company_id == company.id,
                Customer.name == "Venda na Loja"
            ).first()
            
            if existing_customer:
                print(f"✓ Empresa '{company.name}' já possui cliente 'Venda na Loja' (ID: {existing_customer.id})")
                continue
            
            # Criar novo cliente "Venda na Loja"
            new_customer = Customer(
                name="Venda na Loja",
                email=None,
                phone=None,
                cpf=None,
                address=None,
                company_id=company.id,
                is_active=True
            )
            
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            
            print(f"✓ Cliente 'Venda na Loja' criado para empresa '{company.name}' (ID: {new_customer.id})")
        
        print("\n✅ Script concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar clientes: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Criando Cliente Padrão 'Venda na Loja' ===\n")
    create_default_customer()
