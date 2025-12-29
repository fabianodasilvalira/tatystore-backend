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
from app.models.product import Product
from app.models.category import Category
from app.models.customer import Customer
from app.models.sale import Sale, SaleItem, PaymentType, SaleStatus
from app.models.installment import Installment, InstallmentStatus
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

        # 2. Verificar/Criar Empresa Administrativa
        admin_company = db.query(Company).filter(Company.slug == "tatystore-admin").first()
        
        if not admin_company:
            print("🏢 Criando empresa administrativa do sistema...")
            admin_company = Company(
                name="TatyStore System",
                slug="tatystore-admin",
                cnpj="00000000000000",
                email=settings.ADMIN_EMAIL,
                phone="(00) 0000-0000",
                address="System Cloud",
                is_active=True
            )
            db.add(admin_company)
            db.flush()
        
        # 3. Verificar/Criar Usuário Admin
        admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        
        if not admin_user:
            print(f"👤 Criando usuário admin {settings.ADMIN_EMAIL}...")
            admin_user = User(
                name="Administrador Geral",
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                company_id=admin_company.id,
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
    - Permissions and roles (Super Admin, Admin, Gerente, Vendedor)
    - Empresa Principal: Taty Perfumaria
    - 4 usuários (Admin + Gerente + Vendedor + 1 inativo)
    - CATEGORIAS: 6 categorias
    - 15 produtos com categorias e PROMOÇÕES
    - 4 clientes (3 ativos + 1 inativo)
    - Vendas e histórico financeiro simulado
    """
    
    try:
        existing_perms = db.query(Permission).first()
        if existing_perms:
            print("ℹ️  Dados do sistema já foram inicializados anteriormente")
            print("")
            print("=" * 80)
            print("🔑 CREDENCIAIS DE ACESSO")
            print("=" * 80)
            print("🔹 TATY PERFUMARIA:")
            print("   📧 admin@taty.com / admin123 (Administrador)")
            print("   📧 gerente@taty.com / gerente123 (Gerente)")
            print("   📧 vendedor@taty.com / vendedor123 (Vendedor)")
            print("")
            print("💡 ENDPOINTS ÚTEIS:")
            print("   • POST /api/v1/auth/login-json - Fazer login")
            print("   • GET /docs - Documentação interativa (Swagger)")
            print("")
            print("=" * 80)
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
        
        vendedor_inativo = User(
            name=f"Vendedor Inativo {taty.name}",
            email=f"vendedor.inativo@{taty.slug}.com",
            password_hash=hash_password("vendedor123"),
            company_id=taty.id,
            role_id=role_map["Vendedor"].id,
            is_active=False
        )
        db.add(vendedor_inativo)
        
        db.flush()
        
        print("📂 Criando categorias...")
        categories_data = [
            ("Perfumes", "Perfumes e fragrâncias importadas e nacionais"),
            ("Maquiagem", "Produtos de maquiagem para rosto, olhos e lábios"),
            ("Cuidados com a Pele", "Cremes, loções e produtos para cuidados faciais e corporais"),
            ("Cabelos", "Shampoos, condicionadores e tratamentos capilares"),
            ("Acessórios", "Acessórios de beleza, pincéis e esponjas"),
            ("Kits e Presentes", "Kits promocionais e presentes especiais"),
        ]
        
        categories = []
        current_time = get_now_fortaleza_naive()
        for name, description in categories_data:
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
        
        db.flush()
        
        print("📦 Criando produtos...")
        
        # Função auxiliar para criar produtos (adaptada para única empresa)
        products = []
        
        # Categoria: Perfumes (índice 0)
        products.append(Product(
            name="Perfume Clássico Elegance 100ml",
            description="Perfume tradicional com aroma clássico e duradouro",
            sku=f"TATY-PERF-001",
            barcode=f"{taty.id}00001",
            brand="Elegance",
            cost_price=25.00,
            sale_price=79.90,
            is_on_sale=True,
            promotional_price=59.90,
            stock_quantity=150,
            min_stock=20,
            category_id=categories[0].id,
            company_id=taty.id,
            is_active=True
        ))
        
        products.append(Product(
            name="Perfume Importado Luxo 75ml",
            description="Fragrância importada exclusiva com notas florais",
            sku=f"TATY-PERF-002",
            barcode=f"{taty.id}00002",
            brand="Paris Elite",
            cost_price=45.00,
            sale_price=149.90,
            is_on_sale=False,
            promotional_price=None,
            stock_quantity=50,
            min_stock=10,
            category_id=categories[0].id,
            company_id=taty.id,
            is_active=True
        ))
        
        products.append(Product(
            name="Água de Colônia Premium 200ml",
            description="Água de colônia com essência premium e refrescante",
            sku=f"TATY-PERF-003",
            barcode=f"{taty.id}00003",
            brand="Fresh",
            cost_price=15.00,
            sale_price=45.90,
            is_on_sale=True,
            promotional_price=35.90,
            stock_quantity=200,
            min_stock=30,
            category_id=categories[0].id,
            company_id=taty.id,
            is_active=True
        ))
        
        # Categoria: Maquiagem (índice 1)
        products.append(Product(
            name="Base Líquida Mate FPS 30",
            description="Base de alta cobertura com proteção solar",
            sku=f"TATY-MAQ-001",
            barcode=f"{taty.id}00004",
            brand="BeautyPro",
            cost_price=18.00,
            sale_price=55.90,
            is_on_sale=True,
            promotional_price=39.90,
            stock_quantity=80,
            min_stock=15,
            category_id=categories[1].id,
            company_id=taty.id,
            is_active=True
        ))
        
        products.append(Product(
            name="Paleta de Sombras 12 Cores",
            description="Paleta com 12 cores versáteis para qualquer ocasião",
            sku=f"TATY-MAQ-002",
            barcode=f"{taty.id}00005",
            brand="ColorMix",
            cost_price=22.00,
            sale_price=69.90,
            is_on_sale=False,
            promotional_price=None,
            stock_quantity=60,
            min_stock=10,
            category_id=categories[1].id,
            company_id=taty.id,
            is_active=True
        ))
        
        products.append(Product(
            name="Batom Líquido Matte",
            description="Batom líquido de longa duração com acabamento matte",
            sku=f"TATY-MAQ-003",
            barcode=f"{taty.id}00006",
            brand="Kiss Pro",
            cost_price=12.00,
            sale_price=35.90,
            is_on_sale=True,
            promotional_price=25.90,
            stock_quantity=120,
            min_stock=20,
            category_id=categories[1].id,
            company_id=taty.id,
            is_active=True
        ))
        
        # Outros produtos... (simplificado para manter o essencial)
        products.append(Product(
            name="Kit Presente Luxo Completo",
            description="Kit com perfume 100ml + body lotion + sabonete",
            sku=f"TATY-KIT-001",
            barcode=f"{taty.id}00012",
            brand="Gift Collection",
            cost_price=45.00,
            sale_price=129.90,
            is_on_sale=True,
            promotional_price=99.90,
            stock_quantity=8,
            min_stock=10,
            category_id=categories[5].id,
            company_id=taty.id,
            is_active=True
        ))

        for p in products:
            db.add(p)
        
        db.flush()
        
        print("👥 Criando clientes...")
        customers_data = [
            ("João Silva", "joao@email.com", "(11) 98765-4321", "12345678901", "Rua das Flores, 100 - São Paulo, SP", True),
            ("Maria Santos", "maria@email.com", "(11) 97654-3210", "98765432101", "Av. Paulista, 200 - São Paulo, SP", True),
            ("Pedro Costa", "pedro@email.com", "(11) 96543-2109", "55555555555", "Rua Augusta, 300 - São Paulo, SP", True),
            ("Ana Oliveira (Inativo)", "ana@email.com", "(11) 95432-1098", "11111111111", "Rua Teste, 400 - São Paulo, SP", False),
        ]
        
        customers = []
        for name, email, phone, cpf, address, is_active in customers_data:
            unique_cpf = f"{cpf[:-2]}{taty.id:02d}"
            cust = Customer(
                name=name,
                email=f"{email.split('@')[0]}.taty@email.com",
                phone=phone,
                cpf=unique_cpf,
                address=address,
                company_id=taty.id,
                is_active=is_active
            )
            db.add(cust)
            customers.append(cust)
        
        db.flush()
        
        print("💰 Criando Vendas de Teste...")
        
        # Criar algumas vendas simples para popular o dashboard
        active_customers = customers[:3]
        active_products = products[:3]
        
        # Venda 1: À vista
        sale1 = Sale(
            customer_id=active_customers[0].id,
            company_id=taty.id,
            user_id=admin.id,
            payment_type=PaymentType.CASH,
            status=SaleStatus.COMPLETED,
            subtotal=active_products[0].promotional_price,
            discount_amount=0,
            total_amount=active_products[0].promotional_price,
            installments_count=1,
            notes="Venda inicial",
            created_at=get_now_fortaleza_naive()
        )
        db.add(sale1)
        db.flush()
        
        item1 = SaleItem(
            sale_id=sale1.id,
            product_id=active_products[0].id,
            quantity=1,
            unit_price=active_products[0].promotional_price,
            total_price=active_products[0].promotional_price
        )
        db.add(item1)
        
        db.commit()
        print("✅ Dados da Taty Perfumaria inicializados com sucesso!")
        print("")
        print("=" * 80)
        print("🔑 CREDENCIAIS TATY PERFUMARIA")
        print("=" * 80)
        print("   📧 admin@taty.com / admin123")
        print("   📧 gerente@taty.com / gerente123")
        print("   📧 vendedor@taty.com / vendedor123")
        print("")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao inicializar dados: {e}")
        import traceback
        traceback.print_exc()
        raise
