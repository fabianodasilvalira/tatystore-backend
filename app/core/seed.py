"""
Seed data - Inicializa dados do sistema na primeira execução
Usa padrão síncrono para compatibilidade com o FastAPI setup
"""
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.role import Role, role_permissions
from app.models.permission import Permission
from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from app.core.security import hash_password
from app.core.config import get_settings
from app.core.datetime_utils import get_now_fortaleza_naive

settings = get_settings()

def ensure_platform_admin(db: Session):
    """
    Garante que o administrador da plataforma (definido no .env) exista.
    Esta função roda sempre na inicialização, independente do seed.
    """
    try:
        # Verificar se as variáveis de ambiente estão configuradas
        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            print("⚠️  ADMIN_EMAIL ou ADMIN_PASSWORD não configurados. Pulando criação de admin.")
            return

        print(f"🔧 Verificando Administrador da Plataforma ({settings.ADMIN_EMAIL})...")
        
        # 1. Buscar Role de Super Admin
        admin_role = db.query(Role).filter(Role.name == "Super Admin").first()
        if not admin_role:
            # Tentar buscar "Administrador" apenas para migração ou fallback, mas o ideal é criar Super Admin
            print("⚠️  Role 'Super Admin' não encontrada. Criando...")
            admin_role = Role(name="Super Admin", description="Super Administrador da Plataforma")
            db.add(admin_role)
            db.flush()

        # 3. Verificar/Criar Usuário Admin
        admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        
        if not admin_user:
            print(f"👤 Criando usuário admin {settings.ADMIN_EMAIL}...")
            admin_user = User(
                name="Administrador Geral",
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                company_id=None,  # Admin Geral não tem empresa
                role_id=admin_role.id,
                is_active=True,
                created_at=get_now_fortaleza_naive(),
                updated_at=get_now_fortaleza_naive()
            )
            db.add(admin_user)
            db.commit()
            print("✅ Administrador da Plataforma criado com sucesso!")
        else:
            # Atualizar role se necessário
            if admin_user.role_id != admin_role.id:
                print("🔄 Atualizando role do admin para Super Admin...")
                admin_user.role_id = admin_role.id
                db.commit()
            print("✓ Administrador da Plataforma verificado.")
            
    except Exception as e:
        print(f"❌ Erro ao verificar admin da plataforma: {e}")
        db.rollback()

PERMISSIONS = [
    ("products.view", "Pode visualizar produtos"),
    ("products.create", "Pode cadastrar novos produtos"),
    ("products.update", "Pode editar informações gerais de produtos"),
    ("products.update_stock", "Pode alterar o estoque de produtos"),
    ("customers.view", "Pode visualizar clientes"),
    ("customers.create", "Pode cadastrar novos clientes"),
    ("customers.update", "Pode editar dados de clientes"),
    ("sales.create", "Pode registrar vendas"),
    ("sales.cancel", "Pode cancelar vendas"),
    ("reports.view", "Pode visualizar relatórios"),
    ("companies.create", "Pode criar novas empresas"),  # Permissão exclusiva do Super Admin
]

ROLES = ["Super Admin", "Administrador", "Gerente", "Vendedor"]


def seed_data(db: Session):
    """
    Synchronous seed function for system initialization
    
    Cria dados INICIAIS apenas para Taty Perfumaria:
    - Permissões e roles
    - Empresa Principal: Taty Perfumaria
    - Usuários (Admin + Gerente + Vendedor)
    - CATEGORIAS: Apenas as categorias oficiais
    """
    
    try:
        existing_perms = db.query(Permission).first()
        if existing_perms:
            print("ℹ️  Dados do sistema já foram inicializados anteriormente")
            return
        
        print("🔧 Criando permissões e perfis...")
        # Create permissions
        per_objs = []
        for code, desc in PERMISSIONS:
            p = Permission(code=code, description=desc)
            db.add(p)
            per_objs.append(p)
        db.flush()
        
        role_map = {}
        for name in ROLES:
            r = Role(name=name)
            db.add(r)
            role_map[name] = r
        db.flush()
        
        for rname, codes in {
            "Super Admin": [p.code for p in per_objs], # Acesso TOTAL
            "Administrador": [ # Administrador da Empresa (Sem companies.create)
                "products.view", "products.create", "products.update", "products.update_stock",
                "customers.view", "customers.create", "customers.update",
                "sales.create", "sales.cancel", "reports.view"
            ], 
            "Gerente": [
                "products.view", "products.create", "products.update", "products.update_stock",
                "customers.view", "customers.create", "customers.update",
                "sales.create", "sales.cancel", "reports.view"
            ],
            "Vendedor": [  # Permissões básicas
                "products.view", "customers.view", "customers.create", "sales.create"
            ],
        }.items():
            role = role_map[rname]
            role.permissions = [p for p in per_objs if p.code in codes]
        db.flush()
        
        print("🏢 Criando empresa Taty Perfumaria...")
        taty = Company(
            name="Taty Perfumaria",
            slug="taty",
            cnpj="12345678000190",
            email="contato@taty.com",
            phone="(11) 9999-9999",
            address="Rua Taty, 123 - São Paulo, SP",
            is_active=True
        )
        db.add(taty)
        db.flush()
        
        print("👤 Criando usuários...")
        admin = User(
            name=f"Admin {taty.name}",
            email=f"admin@{taty.slug}.com",
            password_hash=hash_password("admin123"),
            company_id=taty.id,
            role_id=role_map["Administrador"].id,
            is_active=True
        )
        db.add(admin)
        
        gerente = User(
            name=f"Gerente {taty.name}",
            email=f"gerente@{taty.slug}.com",
            password_hash=hash_password("gerente123"),
            company_id=taty.id,
            role_id=role_map["Gerente"].id,
            is_active=True
        )
        db.add(gerente)
        
        vendedor = User(
            name=f"Vendedor {taty.name}",
            email=f"vendedor@{taty.slug}.com",
            password_hash=hash_password("vendedor123"),
            company_id=taty.id,
            role_id=role_map["Vendedor"].id,
            is_active=True
        )
        db.add(vendedor)
        
        db.flush()
        
        print("📂 Criando categorias...")
        # Categorias alinhadas com o CSV de importação real
        categories_data = [
            ("Perfumes Masculino", "Fragrâncias masculinas (Boticário, Natura, etc)"),
            ("Perfumes Feminino", "Fragrâncias femininas (Boticário, Natura, etc)"),
            ("Maquiagem", "Produtos de maquiagem para rosto, olhos e lábios"),
            ("Cuidados com a Pele", "Cremes, loções e produtos para cuidados faciais e corporais"),
            ("Cabelos", "Shampoos, condicionadores e tratamentos capilares"),
            ("Kits e Presentes", "Kits promocionais e presentes especiais"),
        ]
        # (Categoria Acessórios removida pois não consta no CSV real)
        
        categories = []
        current_time = get_now_fortaleza_naive()
        for name, description in categories_data:
            # Verifica se categoria já existe para evitar duplicação em re-runs parciais
            existing_cat = db.query(Category).filter(Category.name == name, Category.company_id == taty.id).first()
            if not existing_cat:
                category = Category(
                    name=name,
                    description=description,
                    company_id=taty.id,
                    is_active=True,
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(category)
                categories.append(category)
            else:
                categories.append(existing_cat)
        
        db.flush()
        
        print("✅ Dados do Sistema inicializados (Modo Limpo: Apenas Usuários e Categorias)!")
        print("")
        print("=" * 80)
        print("🔑 CREDENCIAIS TATY PERFUMARIA")
        print("=" * 80)
        print("   📧 admin@taty.com / admin123")
        print("   📧 gerente@taty.com / gerente123")
        print("   📧 vendedor@taty.com / vendedor123")
        print("")
        print("⚠️  SISTEMA PRONTO PARA IMPORTAÇÃO DE PRODUTOS")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao inicializar dados: {e}")
        import traceback
        traceback.print_exc()
        raise
