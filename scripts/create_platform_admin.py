"""
Script para criar o Administrador Geral da Plataforma
Este script cria uma empresa administrativa isolada e o usuário admin principal.
"""
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.core.security import hash_password
from app.core.datetime_utils import get_now_fortaleza_naive

def create_general_admin():
    db = SessionLocal()
    try:
        print("🔧 Iniciando criação do Administrador Geral...")
        
        # 1. Buscar Role de Administrador
        admin_role = db.query(Role).filter(Role.name == "Administrador").first()
        if not admin_role:
            print("❌ Erro: Role 'Administrador' não encontrada. Execute o seed normal primeiro.")
            return

        # 2. Verificar/Criar Empresa Administrativa
        # O admin geral precisa de uma empresa para respeitar a constraint company_id NOT NULL
        admin_company = db.query(Company).filter(Company.slug == "tatystore-admin").first()
        
        if not admin_company:
            print("🏢 Criando empresa administrativa 'TatyStore System'...")
            admin_company = Company(
                name="TatyStore System",
                slug="tatystore-admin",
                cnpj="00000000000000", # CNPJ zerado para sistema
                email="admin@tatystore.com",
                phone="(00) 0000-0000",
                address="System Cloud",
                is_active=True
            )
            db.add(admin_company)
            db.flush()
        else:
            print("ℹ️  Empresa administrativa já existe.")

        # 3. Verificar/Criar Usuário Admin Geral
        admin_email = "admin@tatystore.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            print(f"👤 Criando usuário {admin_email}...")
            # Senha do .env: Fab231282aila@Nubiana
            password_raw = "Fab231282aila@Nubiana" 
            
            admin_user = User(
                name="Administrador Geral",
                email=admin_email,
                password_hash=hash_password(password_raw),
                company_id=admin_company.id,
                role_id=admin_role.id,
                is_active=True,
                created_at=get_now_fortaleza_naive(),
                updated_at=get_now_fortaleza_naive()
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuário criado com sucesso!")
        else:
            print("ℹ️  Usuário administrador já existe.")
            
        print("\n" + "="*50)
        print("🎉 ADMINISTRAÇÃO GERAL CONFIGURADA")
        print("="*50)
        print(f"URL: https://app.tatystore.cloud")
        print(f"Email: {admin_email}")
        print(f"Empresa: {admin_company.name}")
        print("="*50)

    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_general_admin()
