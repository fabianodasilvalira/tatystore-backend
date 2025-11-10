"""
Testes TDD - Fluxo Completo de Empresa
Login → Produtos → Vendas → Parcelas → Relatórios
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.product import Product
from app.models.customer import Customer
from app.models.sale import Sale, SaleItem, PaymentType
from app.models.installment import Installment
from app.core.security import get_password_hash
from datetime import date, datetime


# Fixtures
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Cria tabelas de teste"""
    print("[v0] test_company_flow: Creating test database...")
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    print("[v0] test_company_flow: Database cleaned up")


@pytest.fixture
def client(db):
    """
    Cliente de teste
    """
    print("[v0] test_company_flow: Setting up test client...")
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    original_scheduler = getattr(app, 'scheduler', None)
    print(f"[v0] test_company_flow: Original scheduler: {original_scheduler}")
    app.scheduler = None

    try:
        print("[v0] test_company_flow: Creating test client...")
        test_client = TestClient(app)
        print("[v0] test_company_flow: Test client created successfully")
        yield test_client
    except Exception as e:
        print(f"[v0] test_company_flow: ERROR creating test client: {e}")
        raise
    finally:
        if original_scheduler:
            app.scheduler = original_scheduler
        app.dependency_overrides.clear()
        print("[v0] test_company_flow: Test client teardown complete")


@pytest.fixture
def setup_data(db):
    """Setup inicial: empresa, usuários, produtos, clientes
    """
    print("[v0] test_company_flow: Setting up test data...")
    
    # Roles
    admin_role = Role(name="admin", description="Admin")
    gerente_role = Role(name="gerente", description="Gerente")
    cliente_role = Role(name="cliente", description="Cliente")
    db.add_all([admin_role, gerente_role, cliente_role])
    db.flush()
    print("[v0] test_company_flow: Roles created")
    
    # Empresa
    company = Company(
        name="Test Company",
        slug="test-company",
        cnpj="12345678000100",
        email="company@test.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    print(f"[v0] test_company_flow: Company created with id={company.id}")
    
    # Usuários
    admin_user = User(
        name="Admin",
        email="admin@test.com",
        password_hash=get_password_hash("admin@2025"),
        company_id=company.id,
        role_id=admin_role.id,
        is_active=True
    )
    
    gerente_user = User(
        name="Gerente",
        email="gerente@test.com",
        password_hash=get_password_hash("gerente@2025"),
        company_id=company.id,
        role_id=gerente_role.id,
        is_active=True
    )
    
    db.add_all([admin_user, gerente_user])
    db.flush()
    print(f"[v0] test_company_flow: Users created - admin={admin_user.id}, gerente={gerente_user.id}")
    
    # Produtos
    product = Product(
        name="Produto Teste",
        sku="PROD001",
        cost_price=10.0,
        sale_price=20.0,
        stock_quantity=100,
        company_id=company.id,
        is_active=True
    )
    db.add(product)
    db.flush()
    print(f"[v0] test_company_flow: Product created with id={product.id}")
    
    # Cliente
    customer = Customer(
        name="Cliente Teste",
        email="cliente@test.com",
        cpf="12345678901",
        company_id=company.id,
        is_active=True
    )
    db.add(customer)
    db.commit()
    print(f"[v0] test_company_flow: Customer created with id={customer.id}")
    
    return {
        "company": company,
        "admin_user": admin_user,
        "gerente_user": gerente_user,
        "product": product,
        "customer": customer
    }


def get_auth_headers(token: str) -> dict:
    """
    Helper para retornar header de autorização correto
    """
    return {"Authorization": f"Bearer {token}"}


# TESTES
class TestLogin:
    """Testes de autenticação"""
    
    def test_login_sucesso(self, client, setup_data):
        """Teste: Login e token contém company_id e role_id"""
        print("[v0] TestLogin.test_login_sucesso: Starting...")
        response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "admin@test.com",
                "password": "admin@2025"
            }
        )
        
        print(f"[v0] TestLogin.test_login_sucesso: Response status = {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        token = data["access_token"]
        assert token  # Token deve existir
        assert isinstance(token, str)
        assert len(token) > 0
        print("[v0] TestLogin.test_login_sucesso: PASSED")
    
    def test_login_falha_senha_incorreta(self, client, setup_data):
        """Teste: Login falha com senha incorreta"""
        print("[v0] TestLogin.test_login_falha_senha_incorreta: Starting...")
        response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "admin@test.com",
                "password": "senha_errada"
            }
        )
        
        print(f"[v0] TestLogin.test_login_falha_senha_incorreta: Response status = {response.status_code}")
        assert response.status_code == 401
        print("[v0] TestLogin.test_login_falha_senha_incorreta: PASSED")
    
    def test_login_empresa_inativa(self, client, db, setup_data):
        """Teste: Login falha quando empresa está inativa"""
        print("[v0] TestLogin.test_login_empresa_inativa: Starting...")
        setup_data["company"].is_active = False
        db.commit()
        
        response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "admin@test.com",
                "password": "admin@2025"
            }
        )
        
        print(f"[v0] TestLogin.test_login_empresa_inativa: Response status = {response.status_code}")
        assert response.status_code == 403
        print("[v0] TestLogin.test_login_empresa_inativa: PASSED")


class TestIsolamentoMultiempresa:
    """Testes de isolamento entre empresas"""
    
    def test_usuario_nao_acessa_outra_empresa(self, client, db, setup_data):
        """Teste: Usuário não pode acessar dados de outra empresa (retorna 404)"""
        print("[v0] TestIsolamentoMultiempresa: Starting...")
        # Login
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "admin@test.com",
                "password": "admin@2025"
            }
        )
        print(f"[v0] TestIsolamentoMultiempresa: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        # Criar segunda empresa
        company2 = Company(
            name="Outra Empresa",
            slug="outra-empresa",
            cnpj="98765432000111",
            is_active=True
        )
        db.add(company2)
        db.flush()
        print(f"[v0] TestIsolamentoMultiempresa: Company2 created with id={company2.id}")
        
        product_company2 = Product(
            name="Produto Empresa 2",
            sku="PROD-COMPANY2",
            cost_price=10.0,
            sale_price=20.0,
            stock_quantity=50,
            company_id=company2.id,
            is_active=True
        )
        db.add(product_company2)
        db.commit()
        print(f"[v0] TestIsolamentoMultiempresa: Company2 created with id={company2.id}, Product created with id={product_company2.id}")
        
        # Tentar acessar product da outra empresa com token de usuario1
        response = client.get(
            f"/api/v1/products/{product_company2.id}",
            headers=get_auth_headers(token)
        )
        
        print(f"[v0] TestIsolamentoMultiempresa: Access attempt status = {response.status_code}")
        assert response.status_code in [403, 404]
        print("[v0] TestIsolamentoMultiempresa: PASSED")


class TestProdutos:
    """Testes de gestão de produtos"""
    
    def test_criar_produto_vinculado_empresa(self, client, setup_data):
        """Teste: Criar produto vincula à empresa do usuário"""
        print("[v0] TestProdutos: Starting...")
        # Login
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "gerente@test.com",
                "password": "gerente@2025"
            }
        )
        print(f"[v0] TestProdutos: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        # Criar produto
        response = client.post(
            "/api/v1/products/",
            headers=get_auth_headers(token),
            json={
                "name": "Novo Produto",
                "sku": "PROD002",
                "cost_price": 15.0,
                "sale_price": 30.0,
                "stock_quantity": 50
            }
        )
        
        print(f"[v0] TestProdutos: Create product status = {response.status_code}")
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["company_id"] == setup_data["company"].id
        assert data["name"] == "Novo Produto"
        print("[v0] TestProdutos: PASSED")


class TestVendas:
    """Testes de vendas e estoque"""
    
    def test_compra_reduz_estoque(self, client, db, setup_data):
        """Teste: Compra reduz estoque corretamente"""
        print("[v0] TestVendas.test_compra_reduz_estoque: Starting...")
        # Login
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "gerente@test.com",
                "password": "gerente@2025"
            }
        )
        print(f"[v0] TestVendas.test_compra_reduz_estoque: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        estoque_anterior = setup_data["product"].stock_quantity
        print(f"[v0] TestVendas.test_compra_reduz_estoque: Stock before = {estoque_anterior}")
        
        # Criar venda
        response = client.post(
            "/api/v1/sales/",
            headers=get_auth_headers(token),
            json={
                "customer_id": setup_data["customer"].id,
                "payment_type": "cash",
                "discount_amount": 0,
                "items": [
                    {
                        "product_id": setup_data["product"].id,
                        "quantity": 10,
                        "unit_price": 20.0
                    }
                ]
            }
        )
        
        print(f"[v0] TestVendas.test_compra_reduz_estoque: Create sale status = {response.status_code}")
        assert response.status_code in [200, 201]
        
        # Verificar estoque diminuiu
        db.refresh(setup_data["product"])
        print(f"[v0] TestVendas.test_compra_reduz_estoque: Stock after = {setup_data['product'].stock_quantity}")
        assert setup_data["product"].stock_quantity == estoque_anterior - 10
        print("[v0] TestVendas.test_compra_reduz_estoque: PASSED")
    
    def test_compra_credito_gera_parcelas(self, client, db, setup_data):
        """Teste: Compra à crédito gera parcelas corretamente"""
        print("[v0] TestVendas.test_compra_credito_gera_parcelas: Starting...")
        # Login
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "gerente@test.com",
                "password": "gerente@2025"
            }
        )
        print(f"[v0] TestVendas.test_compra_credito_gera_parcelas: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        # Criar venda a crédito
        response = client.post(
            "/api/v1/sales/",
            headers=get_auth_headers(token),
            json={
                "customer_id": setup_data["customer"].id,
                "payment_type": "credit",
                "installments_count": 3,
                "discount_amount": 0,
                "items": [
                    {
                        "product_id": setup_data["product"].id,
                        "quantity": 6,
                        "unit_price": 20.0
                    }
                ]
            }
        )
        
        print(f"[v0] TestVendas.test_compra_credito_gera_parcelas: Create sale status = {response.status_code}")
        assert response.status_code in [200, 201]
        sale_data = response.json()
        
        # Verificar parcelas foram criadas
        installments = db.query(Installment).filter(
            Installment.sale_id == sale_data["id"]
        ).all()
        
        print(f"[v0] TestVendas.test_compra_credito_gera_parcelas: Installments count = {len(installments)}")
        assert len(installments) == 3
        assert abs(sum(i.amount for i in installments) - 120.0) < 0.01
        print("[v0] TestVendas.test_compra_credito_gera_parcelas: PASSED")


class TestParcelas:
    """Testes de crediário"""
    
    def test_marcar_parcela_paga(self, client, db, setup_data):
        """Teste: Marcar parcela como paga atualiza status"""
        print("[v0] TestParcelas: Starting...")
        # Criar venda a crédito
        sale = Sale(
            customer_id=setup_data["customer"].id,
            company_id=setup_data["company"].id,
            user_id=setup_data["admin_user"].id,
            payment_type=PaymentType.CREDIT,
            total_amount=100.0,
            status="completed"
        )
        db.add(sale)
        db.flush()
        
        installment = Installment(
            sale_id=sale.id,
            customer_id=setup_data["customer"].id,
            company_id=setup_data["company"].id,
            installment_number=1,
            amount=100.0,
            due_date=date.today()
        )
        db.add(installment)
        db.commit()
        print(f"[v0] TestParcelas: Installment created with id={installment.id}")
        
        # Login e marcar como paga
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "gerente@test.com",
                "password": "gerente@2025"
            }
        )
        print(f"[v0] TestParcelas: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        response = client.patch(
            f"/api/v1/installments/{installment.id}/pay",
            headers=get_auth_headers(token)
        )
        
        print(f"[v0] TestParcelas: Pay installment status = {response.status_code}")
        assert response.status_code == 200
        assert response.json()["status"] == "paid"
        assert response.json()["paid_at"] is not None
        print("[v0] TestParcelas: PASSED")


class TestRelatorios:
    """Testes de relatórios"""
    
    def test_relatorio_vendas(self, client, db, setup_data):
        """Teste: Relatório de vendas retorna dados corretos"""
        print("[v0] TestRelatorios: Starting...")
        sale = Sale(
            customer_id=setup_data["customer"].id,
            company_id=setup_data["company"].id,
            user_id=setup_data["admin_user"].id,
            payment_type=PaymentType.CASH,
            discount_amount=20.0,
            total_amount=180.0,
            status="completed",
            created_at=datetime.utcnow()  # Explicitly set created_at
        )
        db.add(sale)
        db.flush()
        
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=setup_data["product"].id,
            quantity=10,
            unit_price=20.0,
            total_price=200.0
        )
        db.add(sale_item)
        db.commit()
        print(f"[v0] TestRelatorios: Sale created with id={sale.id}, created_at={sale.created_at}")
        
        # Login e obter relatório
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={
                "email": "gerente@test.com",
                "password": "gerente@2025"
            }
        )
        print(f"[v0] TestRelatorios: Login status = {login_response.status_code}")
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/reports/sales?period=today",
            headers=get_auth_headers(token)
        )
        
        print(f"[v0] TestRelatorios: Report status = {response.status_code}")
        print(f"[v0] TestRelatorios: Report data = {response.json()}")
        assert response.status_code == 200
        data = response.json()
        if isinstance(data, dict) and "total_sales" in data:
            print(f"[v0] TestRelatorios: total_sales = {data['total_sales']}, total_revenue = {data['total_revenue']}")
            assert data["total_sales"] >= 1
            assert data["total_revenue"] >= 180.0
        else:
            # Report returns list of sales
            assert isinstance(data, list)
            assert len(data) >= 1
        print("[v0] TestRelatorios: PASSED")


class TestCronJob:
    """Testes de tarefas agendadas"""
    
    def test_cron_marcar_vencidas(self, client, db, setup_data):
        """Teste: Parcelas vencidas são marcadas como overdue pelo cron"""
        print("[v0] TestCronJob: Starting...")
        from app.models.installment import InstallmentStatus
        from datetime import date, timedelta
        
        # Criar parcela com vencimento passado
        sale = Sale(
            customer_id=setup_data["customer"].id,
            company_id=setup_data["company"].id,
            user_id=setup_data["admin_user"].id,
            payment_type=PaymentType.CREDIT,
            total_amount=100.0,
            status="completed"
        )
        db.add(sale)
        db.flush()
        
        installment = Installment(
            sale_id=sale.id,
            customer_id=setup_data["customer"].id,
            company_id=setup_data["company"].id,
            installment_number=1,
            amount=100.0,
            due_date=date.today() - timedelta(days=10),
            status=InstallmentStatus.PENDING
        )
        db.add(installment)
        db.commit()
        print(f"[v0] TestCronJob: Overdue installment created with id={installment.id}")
        
        # Chamar cron job
        from app.core.config import settings
        response = client.post(
            "/api/v1/cron/mark-overdue",
            headers={"X-Cron-Secret": settings.CRON_SECRET}
        )
        
        print(f"[v0] TestCronJob: Cron response status = {response.status_code}")
        assert response.status_code == 200
        
        # Verificar que parcela foi marcada como vencida
        db.refresh(installment)
        print(f"[v0] TestCronJob: Installment status after cron = {installment.status}")
        assert installment.status == InstallmentStatus.OVERDUE
        print("[v0] TestCronJob: PASSED")
