"""
Script para criar dados iniciais do sistema:
- Empresa padrão
- Roles (admin, user)
- Permissões
- Usuário admin
"""
import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, Base, async_engine
from app.core.security import hash_password
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.models.permission import Permission
from app.models.associations import role_permissions
import uuid

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("🌱 Iniciando seed de dados...")
        
        company = (await db.execute(select(Company).where(Company.slug == "tatystore"))).scalar_one_or_none()
        if not company:
            print("   📦 Criando empresa padrão...")
            company = Company(
                id=str(uuid.uuid4()),
                slug="tatystore",
                name="Taty Store",
                status="active",
                admin_email="admin@tatystore.com"
            )
            db.add(company)
            await db.flush()
            print(f"   ✓ Empresa criada: {company.name}")
        else:
            print(f"   ✓ Empresa já existe: {company.name}")
        
        admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one_or_none()
        if not admin_role:
            print("   👥 Criando roles...")
            admin_role = Role(id=str(uuid.uuid4()), name="admin")
            user_role = Role(id=str(uuid.uuid4()), name="user")
            db.add_all([admin_role, user_role])
            await db.flush()
            print("   ✓ Roles criadas: admin, user")
        else:
            print("   ✓ Roles já existem")
        
        permissions_data = [
            ("products.create", "Criar produtos"),
            ("products.read", "Visualizar produtos"),
            ("products.update", "Atualizar produtos"),
            ("products.delete", "Deletar produtos"),
            ("customers.create", "Criar clientes"),
            ("customers.read", "Visualizar clientes"),
            ("customers.update", "Atualizar clientes"),
            ("customers.delete", "Deletar clientes"),
            ("sales.create", "Criar vendas"),
            ("sales.read", "Visualizar vendas"),
            ("sales.update", "Atualizar vendas"),
            ("sales.delete", "Deletar vendas"),
            ("reports.read", "Visualizar relatórios"),
            ("users.manage", "Gerenciar usuários"),
            ("settings.manage", "Gerenciar configurações"),
        ]
        
        existing_perms = (await db.execute(select(Permission))).scalars().all()
        if not existing_perms:
            print("   🔐 Criando permissões...")
            permissions = []
            for code, desc in permissions_data:
                perm = Permission(id=str(uuid.uuid4()), code=code, description=desc)
                permissions.append(perm)
                db.add(perm)
            await db.flush()
            
            # Associar todas as permissões ao admin
            for perm in permissions:
                await db.execute(
                    role_permissions.insert().values(role_id=admin_role.id, permission_id=perm.id)
                )
            print(f"   ✓ {len(permissions)} permissões criadas e associadas ao admin")
        else:
            print("   ✓ Permissões já existem")
        
        admin_user = (await db.execute(select(User).where(User.email == "admin@tatystore.com"))).scalar_one_or_none()
        if not admin_user:
            print("   👤 Criando usuário admin...")
            admin_user = User(
                id=str(uuid.uuid4()),
                name="Administrador",
                email="admin@tatystore.com",
                password_hash=hash_password("admin123"),
                company_id=company.id,
                role_id=admin_role.id,
                must_change_password=True
            )
            db.add(admin_user)
            await db.commit()
            print("   ✓ Usuário admin criado!")
            print("\n   📧 Email: admin@tatystore.com")
            print("   🔑 Senha: admin123")
            print("   ⚠️  IMPORTANTE: Mude a senha no primeiro login!\n")
        else:
            print("   ✓ Usuário admin já existe")
        
        await db.commit()
        print("✅ Seed concluído com sucesso!")

async def main():
    print("🚀 Executando seed do banco de dados...")
    try:
        await seed_data()
    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
