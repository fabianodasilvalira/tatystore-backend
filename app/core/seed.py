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

settings = get_settings()

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
    ("companies.create", "Pode criar novas empresas"),  # New permission
]

ROLES = ["Administrador", "Gerente", "Vendedor"]


def seed_data(db: Session):
    """
    Synchronous seed function for system initialization
    
    Cria dados COMPLETOS para testes abrangentes:
    - Permissions and roles (3 roles: Admin, Gerente, Vendedor)
    - Two companies (Taty Perfumaria, Carol Perfumaria)
    - 3 usuários por empresa (Admin + Gerente + Vendedor = 6 usuários)
    - CATEGORIAS: 6 categorias por empresa (Perfumes, Maquiagem, Cuidados com a Pele, etc.)
    - 15 produtos por empresa com categorias e PROMOÇÕES (12 ativos + 3 inativos = 30 produtos totais)
    - 4 clientes por empresa (3 ativos + 1 inativo = 8 clientes totais)
    - 20+ vendas variadas (à vista, crediário, PIX) com histórico de 3 meses
    - Vendas canceladas (2 por empresa)
    - Produtos com baixo estoque (3 por empresa)
    - Parcelas em diferentes estados (pagas, pendentes, vencidas)
    """
    
    try:
        existing_perms = db.query(Permission).first()
        if existing_perms:
            print("ℹ️  Dados do sistema já foram inicializados anteriormente")
            print("")
            print("=" * 80)
            print("🔑 CREDENCIAIS DE ACESSO PARA TESTES")
            print("=" * 80)
            print("")
            print("🔹 TATY PERFUMARIA:")
            print("   📧 admin@taty.com / admin123 (Administrador)")
            print("   📧 gerente@taty.com / gerente123 (Gerente)")
            print("   📧 vendedor@taty.com / vendedor123 (Vendedor)")
            print("")
            print("🔹 CAROL PERFUMARIA:")
            print("   📧 admin@carol.com / admin123 (Administrador)")
            print("   📧 gerente@carol.com / gerente123 (Gerente)")
            print("   📧 vendedor@carol.com / vendedor123 (Vendedor)")
            print("")
            print("💡 ENDPOINTS ÚTEIS:")
            print("   • POST /api/v1/auth/login-json - Fazer login")
            print("   • GET /api/v1/public/test-credentials - Ver todas as credenciais")
            print("   • GET /docs - Documentação interativa (Swagger)")
            print("")
            print("📝 EXEMPLO DE REQUEST:")
            print('   curl -X POST "http://localhost:8000/api/v1/auth/login-json" \\')
            print('        -H "Content-Type: application/json" \\')
            print('        -d \'{"email": "admin@taty.com", "password": "admin123"}\'')
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
            "Administrador": [p.code for p in per_objs],  # Todas as permissões
            "Gerente": [  # Todas as permissões exceto criar empresa (que é Admin)
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
        
        print("🏢 Criando empresas...")
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
        
        carol = Company(
            name="Carol Perfumaria",
            slug="carol",
            cnpj="98765432000150",
            email="contato@carol.com",
            phone="(11) 8888-8888",
            address="Av. Carol, 456 - São Paulo, SP",
            is_active=True
        )
        db.add(carol)
        db.flush()
        
        print("👤 Criando usuários (Admin + Gerente + Vendedor + 1 inativo para cada empresa)...")
        user_map = {}
        for company in [taty, carol]:
            admin = User(
                name=f"Admin {company.name}",
                email=f"admin@{company.slug}.com",
                password_hash=hash_password("admin123"),
                company_id=company.id,
                role_id=role_map["Administrador"].id,  # Usando "Administrador" ao invés de "admin"
                is_active=True
            )
            db.add(admin)
            
            # Gerente
            gerente = User(
                name=f"Gerente {company.name}",
                email=f"gerente@{company.slug}.com",
                password_hash=hash_password("gerente123"),
                company_id=company.id,
                role_id=role_map["Gerente"].id,
                is_active=True
            )
            db.add(gerente)
            
            # Vendedor
            vendedor = User(
                name=f"Vendedor {company.name}",
                email=f"vendedor@{company.slug}.com",
                password_hash=hash_password("vendedor123"),
                company_id=company.id,
                role_id=role_map["Vendedor"].id,
                is_active=True
            )
            db.add(vendedor)
            
            # Vendedor Inativo (para testar bloqueio)
            vendedor_inativo = User(
                name=f"Vendedor Inativo {company.name}",
                email=f"vendedor.inativo@{company.slug}.com",
                password_hash=hash_password("vendedor123"),
                company_id=company.id,
                role_id=role_map["Vendedor"].id,
                is_active=False
            )
            db.add(vendedor_inativo)
            
            user_map[company.slug] = {
                "admin": admin, 
                "gerente": gerente,
                "vendedor": vendedor,
                "vendedor_inativo": vendedor_inativo
            }
        
        db.flush()
        
        print("📂 Criando 6 categorias para cada empresa...")
        categories_data = [
            ("Perfumes", "Perfumes e fragrâncias importadas e nacionais"),
            ("Maquiagem", "Produtos de maquiagem para rosto, olhos e lábios"),
            ("Cuidados com a Pele", "Cremes, loções e produtos para cuidados faciais e corporais"),
            ("Cabelos", "Shampoos, condicionadores e tratamentos capilares"),
            ("Acessórios", "Acessórios de beleza, pincéis e esponjas"),
            ("Kits e Presentes", "Kits promocionais e presentes especiais"),
        ]
        
        category_map = {}
        current_time = datetime.utcnow()
        for company in [taty, carol]:
            company_categories = []
            for name, description in categories_data:
                category = Category(
                    name=name,
                    description=description,
                    company_id=company.id,
                    is_active=True,
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(category)
                company_categories.append(category)
            category_map[company.slug] = company_categories
        
        db.flush()
        
        print("📦 Criando 15 produtos para cada empresa com categorias e PROMOÇÕES...")
        print("   ⭐ Produtos em promoção terão desconto de 10-30%")
        
        # Função auxiliar para criar produtos
        def create_products_for_company(company, categories):
            products = []
            
            # Categoria: Perfumes (índice 0)
            products.append(Product(
                name="Perfume Clássico Elegance 100ml",
                description="Perfume tradicional com aroma clássico e duradouro",
                sku=f"{company.slug.upper()}-PERF-001",
                barcode=f"{company.id}00001",
                brand="Elegance",
                cost_price=25.00,
                sale_price=79.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=59.90,  # 25% de desconto
                stock_quantity=150,
                min_stock=20,
                category_id=categories[0].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Perfume Importado Luxo 75ml",
                description="Fragrância importada exclusiva com notas florais",
                sku=f"{company.slug.upper()}-PERF-002",
                barcode=f"{company.id}00002",
                brand="Paris Elite",
                cost_price=45.00,
                sale_price=149.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=50,
                min_stock=10,
                category_id=categories[0].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Água de Colônia Premium 200ml",
                description="Água de colônia com essência premium e refrescante",
                sku=f"{company.slug.upper()}-PERF-003",
                barcode=f"{company.id}00003",
                brand="Fresh",
                cost_price=15.00,
                sale_price=45.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=35.90,  # 22% de desconto
                stock_quantity=200,
                min_stock=30,
                category_id=categories[0].id,
                company_id=company.id,
                is_active=True
            ))
            
            # Categoria: Maquiagem (índice 1)
            products.append(Product(
                name="Base Líquida Mate FPS 30",
                description="Base de alta cobertura com proteção solar",
                sku=f"{company.slug.upper()}-MAQ-001",
                barcode=f"{company.id}00004",
                brand="BeautyPro",
                cost_price=18.00,
                sale_price=55.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=39.90,  # 29% de desconto
                stock_quantity=80,
                min_stock=15,
                category_id=categories[1].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Paleta de Sombras 12 Cores",
                description="Paleta com 12 cores versáteis para qualquer ocasião",
                sku=f"{company.slug.upper()}-MAQ-002",
                barcode=f"{company.id}00005",
                brand="ColorMix",
                cost_price=22.00,
                sale_price=69.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=60,
                min_stock=10,
                category_id=categories[1].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Batom Líquido Matte",
                description="Batom líquido de longa duração com acabamento matte",
                sku=f"{company.slug.upper()}-MAQ-003",
                barcode=f"{company.id}00006",
                brand="Kiss Pro",
                cost_price=12.00,
                sale_price=35.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=25.90,  # 28% de desconto
                stock_quantity=120,
                min_stock=20,
                category_id=categories[1].id,
                company_id=company.id,
                is_active=True
            ))
            
            # Categoria: Cuidados com a Pele (índice 2)
            products.append(Product(
                name="Creme Hidratante Facial Anti-Idade 50g",
                description="Creme anti-idade com colágeno e vitaminas",
                sku=f"{company.slug.upper()}-SKIN-001",
                barcode=f"{company.id}00007",
                brand="SkinCare Plus",
                cost_price=28.00,
                sale_price=89.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=70,
                min_stock=15,
                category_id=categories[2].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Body Lotion Hidratante 250ml",
                description="Loção corporal com vitamina E e manteiga de karité",
                sku=f"{company.slug.upper()}-SKIN-002",
                barcode=f"{company.id}00008",
                brand="SoftBody",
                cost_price=12.00,
                sale_price=32.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=24.90,  # 24% de desconto
                stock_quantity=100,
                min_stock=20,
                category_id=categories[2].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Sabonete Líquido Neutro 500ml",
                description="Sabonete líquido para todo tipo de pele, pH neutro",
                sku=f"{company.slug.upper()}-SKIN-003",
                barcode=f"{company.id}00009",
                brand="PureClean",
                cost_price=8.00,
                sale_price=22.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=180,
                min_stock=30,
                category_id=categories[2].id,
                company_id=company.id,
                is_active=True
            ))
            
            # Categoria: Cabelos (índice 3)
            products.append(Product(
                name="Shampoo Hidratação Profunda 400ml",
                description="Shampoo com óleo de argan para cabelos ressecados",
                sku=f"{company.slug.upper()}-HAIR-001",
                barcode=f"{company.id}00010",
                brand="HairPro",
                cost_price=15.00,
                sale_price=42.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=32.90,  # 23% de desconto
                stock_quantity=90,
                min_stock=20,
                category_id=categories[3].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Condicionador Reconstrutor 400ml",
                description="Condicionador para cabelos danificados e quimicamente tratados",
                sku=f"{company.slug.upper()}-HAIR-002",
                barcode=f"{company.id}00011",
                brand="HairPro",
                cost_price=16.00,
                sale_price=45.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=85,
                min_stock=20,
                category_id=categories[3].id,
                company_id=company.id,
                is_active=True
            ))
            
            # Categoria: Kits e Presentes (índice 5) - COM BAIXO ESTOQUE
            products.append(Product(
                name="Kit Presente Luxo Completo",
                description="Kit com perfume 100ml + body lotion + sabonete",
                sku=f"{company.slug.upper()}-KIT-001",
                barcode=f"{company.id}00012",
                brand="Gift Collection",
                cost_price=45.00,
                sale_price=129.90,
                is_on_sale=True,  # EM PROMOÇÃO
                promotional_price=99.90,  # 23% de desconto
                stock_quantity=8,  # BAIXO ESTOQUE
                min_stock=10,
                category_id=categories[5].id,
                company_id=company.id,
                is_active=True
            ))
            
            products.append(Product(
                name="Kit Dia das Mães Especial",
                description="Kit especial com 3 produtos para presente",
                sku=f"{company.slug.upper()}-KIT-002",
                barcode=f"{company.id}00013",
                brand="Gift Collection",
                cost_price=35.00,
                sale_price=99.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=5,  # BAIXO ESTOQUE
                min_stock=10,
                category_id=categories[5].id,
                company_id=company.id,
                is_active=True
            ))
            
            # Produtos inativos (descontinuados)
            products.append(Product(
                name="Perfume Descontinuado Antigo",
                description="Produto fora de linha - descontinuado",
                sku=f"{company.slug.upper()}-OLD-001",
                barcode=f"{company.id}00014",
                brand="OldBrand",
                cost_price=30.00,
                sale_price=79.90,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=0,
                min_stock=0,
                category_id=categories[0].id,
                company_id=company.id,
                is_active=False
            ))
            
            products.append(Product(
                name="Loção Corporal Antiga",
                description="Produto descontinuado pela marca",
                sku=f"{company.slug.upper()}-OLD-002",
                barcode=f"{company.id}00015",
                brand="OldBrand",
                cost_price=15.00,
                sale_price=35.00,
                is_on_sale=False,
                promotional_price=None,
                stock_quantity=0,
                min_stock=0,
                category_id=categories[2].id,
                company_id=company.id,
                is_active=False
            ))
            
            return products
        
        product_map = {}
        for company in [taty, carol]:
            categories = category_map[company.slug]
            company_products = create_products_for_company(company, categories)
            
            for product in company_products:
                db.add(product)
            
            product_map[company.slug] = company_products
        
        db.flush()
        
        print("👥 Criando 4 clientes para cada empresa (3 ativos + 1 inativo)...")
        customers_data = [
            ("João Silva", "joao@email.com", "(11) 98765-4321", "12345678901", "Rua das Flores, 100 - São Paulo, SP", True),
            ("Maria Santos", "maria@email.com", "(11) 97654-3210", "98765432101", "Av. Paulista, 200 - São Paulo, SP", True),
            ("Pedro Costa", "pedro@email.com", "(11) 96543-2109", "55555555555", "Rua Augusta, 300 - São Paulo, SP", True),
            ("Ana Oliveira (Inativo)", "ana@email.com", "(11) 95432-1098", "11111111111", "Rua Teste, 400 - São Paulo, SP", False),
        ]
        
        customer_map = {}
        for company in [taty, carol]:
            company_customers = []
            for name, email, phone, cpf, address, is_active in customers_data:
                unique_cpf = f"{cpf[:-2]}{company.id:02d}"
                cust = Customer(
                    name=name,
                    email=f"{email.split('@')[0]}.{company.slug}@email.com",
                    phone=phone,
                    cpf=unique_cpf,
                    address=address,
                    company_id=company.id,
                    is_active=is_active
                )
                db.add(cust)
                company_customers.append(cust)
            customer_map[company.slug] = company_customers
        
        db.flush()
        
        print("💰 Criando 20+ vendas variadas com histórico de 3 meses...")
        print("   💸 Incluindo vendas de produtos em PROMOÇÃO")
        for company in [taty, carol]:
            admin_user = user_map[company.slug]["admin"]
            gerente_user = user_map[company.slug]["gerente"]
            vendedor_user = user_map[company.slug]["vendedor"]
            customers = customer_map[company.slug]
            products = product_map[company.slug]
            
            # Apenas clientes ativos (primeiros 3)
            active_customers = customers[:3]
            # Apenas produtos ativos (primeiros 13)
            active_products = [p for p in products if p.is_active]
            
            sales_scenarios = [
                # Vendas à vista recentes (últimos 10 dias) - INCLUINDO PRODUTOS EM PROMOÇÃO
                (0, PaymentType.CASH, admin_user, active_customers[0], [active_products[0], active_products[1]], [2, 1], 0.10),  # Perfume em promoção
                (2, PaymentType.CASH, vendedor_user, active_customers[1], [active_products[3]], [2], 0.05),  # Base em promoção
                (5, PaymentType.PIX, gerente_user, active_customers[2], [active_products[2], active_products[7]], [1, 2], 0.0),  # Água de colônia + body lotion em promoção
                (7, PaymentType.CASH, vendedor_user, active_customers[0], [active_products[5]], [3], 0.15),  # Batom em promoção
                (10, PaymentType.PIX, admin_user, active_customers[1], [active_products[11]], [1], 0.0),  # Kit em promoção
                
                # Vendas a crediário recentes (3-4 parcelas)
                (12, PaymentType.CREDIT, gerente_user, active_customers[2], [active_products[11], active_products[9]], [1, 1], 0.0, 3),
                (15, PaymentType.CREDIT, vendedor_user, active_customers[0], [active_products[4]], [2], 0.05, 3),
                (18, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[0], active_products[3]], [2, 2], 0.10, 4),
                
                # Vendas do mês passado (30-50 dias atrás)
                (30, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[2], active_products[6]], [3, 1], 0.05),
                (35, PaymentType.PIX, gerente_user, active_customers[0], [active_products[8]], [4], 0.0),
                (40, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[1], active_products[4]], [1, 2], 0.0, 5),
                (42, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[7]], [3], 0.10),
                (45, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[5], active_products[9]], [2, 1], 0.05, 4),
                
                # Vendas de 2 meses atrás (60-75 dias)
                (60, PaymentType.CASH, admin_user, active_customers[1], [active_products[0]], [5], 0.10),
                (62, PaymentType.PIX, vendedor_user, active_customers[2], [active_products[2], active_products[3]], [2, 3], 0.0),
                (65, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[6]], [4], 0.0, 4),
                (68, PaymentType.CASH, admin_user, active_customers[1], [active_products[7], active_products[8]], [2, 1], 0.15),
                (70, PaymentType.CREDIT, vendedor_user, active_customers[2], [active_products[10]], [3], 0.05, 5),
                
                # Vendas de 3 meses atrás (80-90 dias)
                (80, PaymentType.PIX, gerente_user, active_customers[0], [active_products[9], active_products[11]], [2, 2], 0.0),
                (85, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[1]], [5], 0.10, 5),
                (87, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[0], active_products[5]], [3, 2], 0.05),
                (90, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[2], active_products[4]], [1, 3], 0.0, 4),
            ]
            
            created_sales = []
            for scenario in sales_scenarios:
                days_ago = scenario[0]
                payment_type = scenario[1]
                user = scenario[2]
                customer = scenario[3]
                sale_products = scenario[4]
                quantities = scenario[5]
                discount_percent = scenario[6]
                installments_count = scenario[7] if len(scenario) > 7 else 1
                
                # Calcular valores usando preço promocional se aplicável
                subtotal = sum(
                    (p.promotional_price if p.is_on_sale and p.promotional_price else p.sale_price) * q 
                    for p, q in zip(sale_products, quantities)
                )
                discount = subtotal * discount_percent
                total = subtotal - discount
                
                # Criar venda
                sale = Sale(
                    customer_id=customer.id,
                    company_id=company.id,
                    user_id=user.id,
                    payment_type=payment_type,
                    status=SaleStatus.COMPLETED,
                    subtotal=subtotal,
                    discount_amount=discount,
                    total_amount=total,
                    installments_count=installments_count,
                    notes=f"Venda de teste - {payment_type.value}",
                    created_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                db.add(sale)
                db.flush()
                created_sales.append(sale)
                
                # Adicionar itens da venda
                for product, quantity in zip(sale_products, quantities):
                    # Usar preço promocional se aplicável
                    unit_price = product.promotional_price if product.is_on_sale and product.promotional_price else product.sale_price
                    item = SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=unit_price * quantity
                    )
                    db.add(item)
                
                # Criar parcelas para vendas a crediário
                if payment_type == PaymentType.CREDIT:
                    installment_amount = total / installments_count
                    
                    for inst_num in range(1, installments_count + 1):
                        due_date = (datetime.utcnow() - timedelta(days=days_ago) + timedelta(days=30 * inst_num)).date()
                        days_until_due = (due_date - datetime.utcnow().date()).days
                        
                        # Determinar status da parcela
                        if inst_num == 1 and days_ago >= 60:
                            # Primeira parcela de vendas antigas: paga
                            status = InstallmentStatus.PAID
                            paid_at = datetime.utcnow() - timedelta(days=days_ago - 30)
                        elif days_until_due < -10:
                            # Parcelas muito vencidas
                            status = InstallmentStatus.OVERDUE
                            paid_at = None
                        elif days_until_due < 0:
                            # Parcela recém vencida
                            status = InstallmentStatus.OVERDUE
                            paid_at = None
                        else:
                            # Parcela pendente
                            status = InstallmentStatus.PENDING
                            paid_at = None
                        
                        installment = Installment(
                            sale_id=sale.id,
                            customer_id=customer.id,
                            company_id=company.id,
                            installment_number=inst_num,
                            amount=installment_amount,
                            due_date=due_date,
                            status=status,
                            paid_at=paid_at
                        )
                        db.add(installment)
            
            print(f"   🚫 Criando vendas canceladas para {company.name}...")
            for i in range(2):
                days_ago = 20 + (i * 5)
                customer = active_customers[i]
                
                subtotal = active_products[i].sale_price * 2
                discount = 0.0
                total = subtotal
                
                cancelled_sale = Sale(
                    customer_id=customer.id,
                    company_id=company.id,
                    user_id=admin_user.id,
                    payment_type=PaymentType.CASH,
                    status=SaleStatus.CANCELLED,
                    subtotal=subtotal,
                    discount_amount=discount,
                    total_amount=total,
                    installments_count=1,
                    notes="Venda cancelada para teste",
                    created_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                db.add(cancelled_sale)
                db.flush()
                
                # Adicionar item
                item = SaleItem(
                    sale_id=cancelled_sale.id,
                    product_id=active_products[i].id,
                    quantity=2,
                    unit_price=active_products[i].sale_price,
                    total_price=subtotal
                )
                db.add(item)
        
        db.commit()
        print("✅ Dados do sistema inicializados com sucesso!")
        print("")
        print("=" * 80)
        print("📋 RESUMO COMPLETO DOS DADOS CRIADOS")
        print("=" * 80)
        print("")
        print("🏢 EMPRESAS: 2")
        print("   • Taty Perfumaria (slug: taty)")
        print("   • Carol Perfumaria (slug: carol)")
        print("")
        print("👤 USUÁRIOS: 8 (4 por empresa)")
        print("")
        print("🔑 CREDENCIAIS DE ACESSO:")
        print("")
        print("   🔹 TATY PERFUMARIA:")
        print("      📧 admin@taty.com / admin123 (Administrador)")
        print("      📧 gerente@taty.com / gerente123 (Gerente)")
        print("      📧 vendedor@taty.com / vendedor123 (Vendedor)")
        print("      📧 vendedor.inativo@taty.com / vendedor123 (Vendedor - INATIVO)")
        print("")
        print("   🔹 CAROL PERFUMARIA:")
        print("      📧 admin@carol.com / admin123 (Administrador)")
        print("      📧 gerente@carol.com / gerente123 (Gerente)")
        print("      📧 vendedor@carol.com / vendedor123 (Vendedor)")
        print("      📧 vendedor.inativo@carol.com / vendedor123 (Vendedor - INATIVO)")
        print("")
        print("📂 CATEGORIAS: 12 (6 por empresa)")
        print("   • Perfumes")
        print("   • Maquiagem")
        print("   • Cuidados com a Pele")
        print("   • Cabelos")
        print("   • Acessórios")
        print("   • Kits e Presentes")
        print("")
        print("📦 PRODUTOS: 30 (15 por empresa)")
        print("   • 13 produtos ATIVOS com estoque")
        print("   • ⭐ 6 produtos EM PROMOÇÃO por empresa (desconto de 10-30%)")
        print("   • 2 produtos com BAIXO ESTOQUE (≤10 unidades)")
        print("   • 2 produtos INATIVOS (descontinuados)")
        print("")
        print("⭐ PROMOÇÕES ATIVAS:")
        print("   • Perfume Clássico Elegance: R$ 79,90 → R$ 59,90 (25% OFF)")
        print("   • Água de Colônia Premium: R$ 45,90 → R$ 35,90 (22% OFF)")
        print("   • Base Líquida Mate: R$ 55,90 → R$ 39,90 (29% OFF)")
        print("   • Batom Líquido Matte: R$ 35,90 → R$ 25,90 (28% OFF)")
        print("   • Body Lotion: R$ 32,90 → R$ 24,90 (24% OFF)")
        print("   • Shampoo Hidratação: R$ 42,90 → R$ 32,90 (23% OFF)")
        print("   • Kit Presente Luxo: R$ 129,90 → R$ 99,90 (23% OFF)")
        print("")
        print("👥 CLIENTES: 8 (4 por empresa)")
        print("   • 3 clientes ativos")
        print("   • 1 cliente INATIVO")
        print("")
        print("💰 VENDAS: ~44 vendas totais (~22 por empresa)")
        print("   • Vendas à vista (CASH): ~12 por empresa")
        print("   • Vendas via PIX: ~6 por empresa")
        print("   • Vendas a crediário (CREDIT): ~10 por empresa")
        print("   • Vendas CANCELADAS: 2 por empresa")
        print("   • 💸 Vendas incluem produtos em PROMOÇÃO")
        print("   • Histórico: 3 meses completos")
        print("")
        print("📊 PARCELAS: ~80-100 parcelas totais")
        print("   ✅ Pagas (PAID): Primeiras parcelas de vendas antigas")
        print("   ⏳ Pendentes (PENDING): Vencimento futuro")
        print("   ⚠️  Vencidas (OVERDUE): Vencimento passado")
        print("")
        print("🎯 CENÁRIOS DE TESTE COBERTOS:")
        print("   ✅ Login multi-tenant (Admin, Gerente, Vendedor)")
        print("   ✅ Isolamento por empresa")
        print("   ✅ Sistema de CATEGORIAS completo")
        print("   ✅ Produtos com PROMOÇÕES ativas")
        print("   ✅ Produtos com baixo estoque")
        print("   ✅ Produtos inativos")
        print("   ✅ Clientes inativos")
        print("   ✅ Usuários inativos (bloqueio de login)")
        print("   ✅ Vendas canceladas")
        print("   ✅ Vendas de produtos em promoção")
        print("   ✅ Crediário com parcelas vencidas")
        print("   ✅ Relatórios de vendas, lucro, produtos mais vendidos")
        print("   ✅ Relatórios por categoria")
        print("   ✅ Relatórios de inadimplência")
        print("   ✅ Histórico temporal para análises")
        print("")
        print("💡 ENDPOINTS ÚTEIS:")
        print("   • POST /api/v1/auth/login-json - Fazer login")
        print("   • GET /api/v1/categories - Listar categorias")
        print("   • GET /api/v1/products/on-sale - Produtos em promoção")
        print("   • GET /api/v1/public/test-credentials - Ver todas as credenciais")
        print("   • GET /docs - Documentação interativa (Swagger)")
        print("")
        print("📝 EXEMPLO DE REQUEST:")
        print('   curl -X POST "http://localhost:8000/api/v1/auth/login-json" \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"email": "admin@taty.com", "password": "admin123"}\'')
        print("")
        print("=" * 80)
        print("✅ Sistema 100% pronto para testes completos com CATEGORIAS e PROMOÇÕES!")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao inicializar dados: {e}")
        import traceback
        traceback.print_exc()
        raise
