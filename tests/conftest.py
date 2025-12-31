import os
os.environ["TESTING"] = "true"

"""
Configuração de fixtures para testes do sistema TatyStore
Todas as fixtures compartilhadas entre os testes estão aqui
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.company import Company
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.product import Product
from app.models.customer import Customer
from app.models.sale import Sale, SaleItem
from app.models.installment import Installment

# Banco de dados em memória para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Fixture que cria um banco de dados limpo para cada teste
    """
    print("[v0] Creating test database...")
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        print("[v0] Test database cleaned up")


@pytest.fixture(scope="function")
def client(db):
    """
    Fixture que cria um cliente de teste do FastAPI
    Fixed TestClient initialization - pass app as positional argument, not keyword
    """
    print("[v0] Setting up test client...")
    print("[v0] Registered Routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"[v0] Route: {route.path} {route.methods}")
        else:
            print(f"[v0] Route: {route.path} (Mount/Other)")
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    print("[v0] Overriding get_db dependency...")
    app.dependency_overrides[get_db] = override_get_db
    
    # Disable scheduler for tests
    original_scheduler = getattr(app, 'scheduler', None)
    print(f"[v0] Original scheduler: {original_scheduler}")
    app.scheduler = None
    
    try:
        print("[v0] Creating TestClient instance...")
        test_client = TestClient(app)
        print("[v0] TestClient created successfully")
        yield test_client
    except Exception as e:
        print(f"[v0] ERROR creating TestClient: {e}")
        raise
    finally:
        if original_scheduler:
            app.scheduler = original_scheduler
        app.dependency_overrides.clear()
        print("[v0] TestClient teardown complete")


@pytest.fixture(scope="function")
def test_roles(db):
    """
    Cria os perfis de teste: Admin, Gerente, Usuario
    Adicionando permissões ao commit para evitar lazy loading
    """
    print("[v0] Creating test roles...")
    super_admin_role = Role(name="Super Admin", description="Administrador Supremo do Sistema")
    admin_role = Role(name="Administrador", description="Administrador com acesso total")
    manager_role = Role(name="Gerente", description="Gerente com acesso intermediário")
    user_role = Role(name="usuario", description="Usuário básico")
    
    db.add_all([super_admin_role, admin_role, manager_role, user_role])
    db.commit()
    db.refresh(super_admin_role)
    db.refresh(admin_role)
    db.refresh(manager_role)
    db.refresh(user_role)
    
    return {
        "super_admin": super_admin_role,
        "admin": admin_role,
        "gerente": manager_role,
        "usuario": user_role
    }


@pytest.fixture(scope="function")
def test_company1(db):
    """
    Cria primeira empresa de teste
    """
    print("[v0] Creating test company 1...")
    company = Company(
        name="Empresa Teste 1",
        slug="empresa-teste-1",
        cnpj="12345678000100",
        email="contato@empresa1.com",
        phone="11999999999",
        is_active=True
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"[v0] Company 1 created with id={company.id}")
    return company


@pytest.fixture(scope="function")
def test_company2(db):
    """
    Cria segunda empresa de teste (para testar isolamento)
    """
    print("[v0] Creating test company 2...")
    company = Company(
        name="Empresa Teste 2",
        slug="empresa-teste-2",
        cnpj="98765432000199",
        email="contato@empresa2.com",
        phone="11888888888",
        is_active=True
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"[v0] Company 2 created with id={company.id}")
    return company


@pytest.fixture(scope="function")
def test_super_admin_user(db, test_roles):
    """
    Cria usuário super administrador do sistema
    """
    user = User(
        name="Super Admin Teste",
        email="superadmin@teste.com",
        password_hash=get_password_hash("Admin@123"),
        company_id=None,  # Super Admin não tem empresa
        role_id=test_roles["super_admin"].id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin_user(db, test_company1, test_roles):
    """
    Cria usuário administrador de teste
    """
    print("[v0] Creating admin user...")
    user = User(
        name="Admin Teste",
        email="admin@teste.com",
        password_hash=get_password_hash("admin123"),
        company_id=test_company1.id,
        role_id=test_roles["admin"].id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[v0] Admin user created with id={user.id}")
    return user


@pytest.fixture(scope="function")
def test_manager_user(db, test_company1, test_roles):
    """
    Cria usuário gerente de teste
    """
    print("[v0] Creating manager user...")
    user = User(
        name="Gerente Teste",
        email="gerente@teste.com",
        password_hash=get_password_hash("gerente123"),
        company_id=test_company1.id,
        role_id=test_roles["gerente"].id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[v0] Manager user created with id={user.id}")
    return user


@pytest.fixture(scope="function")
def test_user(db, test_company1, test_roles):
    """
    Cria usuário comum de teste
    """
    print("[v0] Creating regular user...")
    user = User(
        name="Usuario Teste",
        email="usuario@teste.com",
        password_hash=get_password_hash("usuario123"),
        company_id=test_company1.id,
        role_id=test_roles["usuario"].id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[v0] Regular user created with id={user.id}")
    return user


@pytest.fixture(scope="function")
def test_user_company2(db, test_company2, test_roles):
    """
    Cria usuário da empresa 2 (para testar isolamento)
    """
    print("[v0] Creating company2 user...")
    user = User(
        name="Usuario Empresa 2",
        email="user@empresa2.com",
        password_hash=get_password_hash("user123"),
        company_id=test_company2.id,
        role_id=test_roles["usuario"].id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[v0] Company2 user created with id={user.id}")
    return user


@pytest.fixture(scope="function")
def super_admin_token(client, test_super_admin_user):
    """
    Obtém token JWT do super administrador
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_super_admin_user.email, "password": "Admin@123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, test_admin_user):
    """
    Obtém token JWT do administrador
    """
    print("[v0] Getting admin token...")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "admin123"}
    )
    print(f"[v0] Admin login response status: {response.status_code}")
    if response.status_code != 200:
        print(f"[v0] Admin login error: {response.text}")
    token = response.json()["access_token"]
    print(f"[v0] Admin token obtained")
    return token


@pytest.fixture(scope="function")
def manager_token(client, test_manager_user):
    """
    Obtém token JWT do gerente
    """
    print("[v0] Getting manager token...")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "gerente@teste.com", "password": "gerente123"}
    )
    print(f"[v0] Manager login response status: {response.status_code}")
    token = response.json()["access_token"]
    print(f"[v0] Manager token obtained")
    return token


@pytest.fixture(scope="function")
def user_token(client, test_user):
    """
    Obtém token JWT do usuário comum
    """
    print("[v0] Getting user token...")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "usuario@teste.com", "password": "usuario123"}
    )
    print(f"[v0] User login response status: {response.status_code}")
    token = response.json()["access_token"]
    print(f"[v0] User token obtained")
    return token


@pytest.fixture(scope="function")
def company2_token(client, test_user_company2):
    """
    Obtém token JWT do usuário da empresa 2
    """
    print("[v0] Getting company2 token...")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@empresa2.com", "password": "user123"}
    )
    print(f"[v0] Company2 login response status: {response.status_code}")
    token = response.json()["access_token"]
    print(f"[v0] Company2 token obtained")
    return token


@pytest.fixture(scope="function")
def test_product(db, test_company1):
    """
    Cria produto de teste
    """
    print("[v0] Creating test product...")
    product = Product(
        name="Produto Teste",
        description="Descrição do produto teste",
        sku="PROD-001",
        barcode="7891234567890",
        cost_price=10.00,
        sale_price=20.00,
        stock_quantity=100,
        min_stock=10,
        company_id=test_company1.id,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    print(f"[v0] Product created with id={product.id}")
    return product


@pytest.fixture(scope="function")
def test_product_company2(db, test_company2):
    """
    Cria produto da empresa 2
    """
    print("[v0] Creating company2 product...")
    product = Product(
        name="Produto Empresa 2",
        description="Produto da segunda empresa",
        sku="PROD-002",
        barcode="7891234567891",
        cost_price=15.00,
        sale_price=30.00,
        stock_quantity=50,
        min_stock=5,
        company_id=test_company2.id,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    print(f"[v0] Company2 product created with id={product.id}")
    return product


@pytest.fixture(scope="function")
def test_customer(db, test_company1):
    """
    Cria cliente de teste
    """
    print("[v0] Creating test customer...")
    customer = Customer(
        name="Cliente Teste",
        email="cliente@teste.com",
        cpf="12345678901",
        phone="11999999999",
        company_id=test_company1.id,
        is_active=True
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    print(f"[v0] Customer created with id={customer.id}")
    return customer


@pytest.fixture(scope="function")
def test_customer2(db, test_company2):
    """
    Cria cliente da empresa 2
    """
    print("[v0] Creating test customer for company 2...")
    customer = Customer(
        name="Cliente Empresa 2",
        email="cliente@empresa2.com",
        cpf="98765432109",
        phone="11888888888",
        company_id=test_company2.id,
        is_active=True
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    print(f"[v0] Customer2 created with id={customer.id}")
    return customer


@pytest.fixture(scope="function")
def test_seller_user(db, test_company1, test_roles):
    """
    Cria usuário vendedor de teste
    """
    print("[v0] Creating seller user...")
    seller_role = db.query(Role).filter(Role.name == "Vendedor").first()
    if not seller_role:
        seller_role = Role(name="Vendedor", description="Vendedor")
        db.add(seller_role)
        db.commit()
        db.refresh(seller_role)
    
    user = User(
        name="Vendedor Teste",
        email="vendedor@teste.com",
        password_hash=get_password_hash("vendedor123"),
        company_id=test_company1.id,
        role_id=seller_role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[v0] Seller user created with id={user.id}")
    return user


@pytest.fixture(scope="function")
def seller_token(client, test_seller_user):
    """
    Obtém token JWT do vendedor
    """
    print("[v0] Getting seller token...")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "vendedor@teste.com", "password": "vendedor123"}
    )
    print(f"[v0] Seller login response status: {response.status_code}")
    if response.status_code != 200:
        print(f"[v0] Seller login error: {response.text}")
    token = response.json()["access_token"]
    print(f"[v0] Seller token obtained")
    return token


@pytest.fixture(scope="function")
def test_product2(db, test_company2):
    """
    Alias para test_product_company2 para manter compatibilidade
    """
    print("[v0] Creating product2...")
    product = Product(
        name="Produto Empresa 2",
        description="Produto da segunda empresa",
        sku="PROD-002",
        barcode="7891234567891",
        cost_price=15.00,
        sale_price=30.00,
        stock_quantity=50,
        min_stock=5,
        company_id=test_company2.id,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    print(f"[v0] Product2 created with id={product.id}")
    return product


@pytest.fixture(scope="function")
def test_sale(db, test_company1, test_customer, test_product, test_admin_user):
    """
    Cria uma venda de teste
    """
    print("[v0] Creating test sale...")
    from app.models.sale import Sale, SaleItem, PaymentType, SaleStatus
    
    sale = Sale(
        customer_id=test_customer.id,
        company_id=test_company1.id,
        user_id=test_admin_user.id,
        payment_type=PaymentType.PIX,
        status=SaleStatus.COMPLETED,
        subtotal=40.00,
        discount_amount=0.00,
        total_amount=40.00,
        installments_count=1
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    
    sale_item = SaleItem(
        sale_id=sale.id,
        product_id=test_product.id,
        quantity=2,
        unit_price=20.00,
        total_price=40.00
    )
    db.add(sale_item)
    db.commit()
    
    print(f"[v0] Test sale created with id={sale.id}")
    return sale


@pytest.fixture(scope="function")
def test_company(db):
    """
    Alias para test_company1 para compatibilidade
    """
    print("[v0] Creating test company (alias)...")
    company = Company(
        name="Empresa Teste",
        slug="empresa-teste",
        cnpj="11111111000111",
        email="contato@empresa.com",
        phone="11999999999",
        is_active=True
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"[v0] Company created with id={company.id}")
    return company


def get_auth_headers(token: str) -> dict:
    """
    Corrected helper to return proper Authorization header with Bearer token
    """
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_category(db, test_company1):
    """
    Cria categoria de teste
    """
    print("[v0] Creating test category...")
    from app.models.category import Category
    category = Category(
        name="Categoria Teste",
        description="Descrição da categoria teste",
        company_id=test_company1.id,
        is_active=True
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    print(f"[v0] Category created with id={category.id}")
    return category


@pytest.fixture(scope="function")
def test_category_company2(db, test_company2):
    """
    Cria categoria da empresa 2
    """
    print("[v0] Creating test category for company 2...")
    from app.models.category import Category
    category = Category(
        name="Categoria Empresa 2",
        description="Descrição da categoria empresa 2",
        company_id=test_company2.id,
        is_active=True
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    print(f"[v0] Category2 created with id={category.id}")
    return category

