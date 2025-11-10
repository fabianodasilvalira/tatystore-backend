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
    - 12 produtos por empresa (10 ativos + 2 inativos = 24 produtos totais)
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
        
        print("📦 Criando 12 produtos para cada empresa (10 ativos + 2 inativos)...")
        products_data = [
            # Produtos normais
            ("Perfume Clássico 100ml", "Perfume tradicional com aroma clássico", 25.00, 59.90, 150, 20, True),
            ("Água de Colônia Premium 200ml", "Água de colônia com essência premium", 15.00, 39.90, 200, 20, True),
            ("Desodorante Antitranspirante", "Desodorante com proteção 24h", 8.00, 19.90, 300, 20, True),
            ("Body Lotion Hidratante 250ml", "Loção corporal com vitamina E", 12.00, 29.90, 100, 20, True),
            ("Sabonete Líquido Neutro 500ml", "Sabonete líquido para todo tipo de pele", 5.00, 12.90, 250, 20, True),
            ("Creme Hidratante Facial 50g", "Creme anti-idade com FPS 30", 18.00, 45.00, 80, 20, True),
            ("Perfume Importado 75ml", "Fragrância importada exclusiva", 45.00, 129.90, 50, 20, True),
            # Produtos com baixo estoque (para testar alertas)
            ("Kit Presente Luxo", "Kit com perfume + body lotion", 35.00, 89.90, 8, 20, True),
            ("Óleo Corporal Relaxante 100ml", "Óleo com essências naturais", 20.00, 49.90, 12, 20, True),
            ("Colônia Infantil 100ml", "Fragrância suave para crianças", 10.00, 24.90, 5, 20, True),
            # Produtos inativos (para testar filtros)
            ("Perfume Descontinuado", "Produto fora de linha", 30.00, 79.90, 0, 20, False),
            ("Loção Antiga", "Produto descontinuado", 15.00, 35.00, 0, 20, False),
        ]
        
        product_map = {}
        for company in [taty, carol]:
            company_products = []
            for i, (name, desc, cost, price, stock, min_stock, is_active) in enumerate(products_data):
                prod = Product(
                    name=name,
                    description=desc,
                    sku=f"{company.slug.upper()}-{i+1:03d}",
                    barcode=f"{company.id}{i:05d}",
                    cost_price=cost,
                    sale_price=price,
                    stock_quantity=stock,
                    min_stock=min_stock,
                    company_id=company.id,
                    is_active=is_active
                )
                db.add(prod)
                company_products.append(prod)
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
        for company in [taty, carol]:
            admin_user = user_map[company.slug]["admin"]
            gerente_user = user_map[company.slug]["gerente"]
            vendedor_user = user_map[company.slug]["vendedor"]
            customers = customer_map[company.slug]
            products = product_map[company.slug]
            
            # Apenas clientes ativos (primeiros 3)
            active_customers = customers[:3]
            # Apenas produtos ativos (primeiros 10)
            active_products = [p for p in products if p.is_active]
            
            sales_scenarios = [
                # Vendas à vista recentes (últimos 10 dias)
                (0, PaymentType.CASH, admin_user, active_customers[0], [active_products[0], active_products[1]], [2, 1], 0.10),
                (2, PaymentType.CASH, vendedor_user, active_customers[1], [active_products[2]], [3], 0.05),
                (5, PaymentType.PIX, gerente_user, active_customers[2], [active_products[3], active_products[4]], [1, 2], 0.0),
                (7, PaymentType.CASH, vendedor_user, active_customers[0], [active_products[5]], [2], 0.15),
                (10, PaymentType.PIX, admin_user, active_customers[1], [active_products[6]], [1], 0.0),
                
                # Vendas a crediário recentes (3-4 parcelas)
                (12, PaymentType.CREDIT, gerente_user, active_customers[2], [active_products[7], active_products[8]], [1, 1], 0.0, 3),
                (15, PaymentType.CREDIT, vendedor_user, active_customers[0], [active_products[9]], [2], 0.05, 3),
                (18, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[0], active_products[1]], [2, 2], 0.10, 4),
                
                # Vendas do mês passado (30-50 dias atrás)
                (30, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[2], active_products[3]], [3, 1], 0.05),
                (35, PaymentType.PIX, gerente_user, active_customers[0], [active_products[4]], [4], 0.0),
                (40, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[5], active_products[6]], [1, 2], 0.0, 5),
                (42, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[7]], [3], 0.10),
                (45, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[8], active_products[9]], [2, 1], 0.05, 4),
                
                # Vendas de 2 meses atrás (60-75 dias)
                (60, PaymentType.CASH, admin_user, active_customers[1], [active_products[0]], [5], 0.10),
                (62, PaymentType.PIX, vendedor_user, active_customers[2], [active_products[1], active_products[2]], [2, 3], 0.0),
                (65, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[3]], [4], 0.0, 4),
                (68, PaymentType.CASH, admin_user, active_customers[1], [active_products[4], active_products[5]], [2, 1], 0.15),
                (70, PaymentType.CREDIT, vendedor_user, active_customers[2], [active_products[6]], [3], 0.05, 5),
                
                # Vendas de 3 meses atrás (80-90 dias)
                (80, PaymentType.PIX, gerente_user, active_customers[0], [active_products[7], active_products[8]], [2, 2], 0.0),
                (85, PaymentType.CREDIT, admin_user, active_customers[1], [active_products[9]], [5], 0.10, 5),
                (87, PaymentType.CASH, vendedor_user, active_customers[2], [active_products[0], active_products[1]], [3, 2], 0.05),
                (90, PaymentType.CREDIT, gerente_user, active_customers[0], [active_products[2], active_products[3]], [1, 3], 0.0, 4),
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
                
                # Calcular valores
                subtotal = sum(p.sale_price * q for p, q in zip(sale_products, quantities))
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
                    item = SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.sale_price,
                        total_price=product.sale_price * quantity
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
        print("📦 PRODUTOS: 24 (12 por empresa)")
        print("   • 10 produtos ativos com estoque normal")
        print("   • 3 produtos com BAIXO ESTOQUE (≤20 unidades)")
        print("   • 2 produtos INATIVOS (descontinuados)")
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
        print("   ✅ Produtos com baixo estoque")
        print("   ✅ Produtos inativos")
        print("   ✅ Clientes inativos")
        print("   ✅ Usuários inativos (bloqueio de login)")
        print("   ✅ Vendas canceladas")
        print("   ✅ Crediário com parcelas vencidas")
        print("   ✅ Relatórios de vendas, lucro, produtos mais vendidos")
        print("   ✅ Relatórios de inadimplência")
        print("   ✅ Histórico temporal para análises")
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
        print("✅ Sistema 100% pronto para testes completos!")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao inicializar dados: {e}")
        import traceback
        traceback.print_exc()
        raise
