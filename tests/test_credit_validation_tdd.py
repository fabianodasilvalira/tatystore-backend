"""
Testes TDD para validação condicional de clientes em vendas a crediário

Testa a lógica de negócio diretamente usando pytest e fixtures
"""

import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.company import Company
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.models.sale import Sale, SaleItem
from app.models.installment import Installment
from app.models.category import Category
from app.models.stock_movement import StockMovement
from app.schemas.sale import SaleCreate, SaleItemIn
from app.api.v1.endpoints.sales import create_sale


# Usar o banco de dados real para testes (PostgreSQL)
from app.core.database import SessionLocal

@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco de dados de teste usando o banco real"""
    session = SessionLocal()
    try:
        yield session
        # Rollback para não afetar outros testes
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def test_company(db_session):
    """Cria uma empresa de teste"""
    import time
    timestamp = str(int(time.time() * 1000))  # milliseconds
    company = Company(
        name=f"Empresa Teste {timestamp}",
        slug=f"empresa-teste-{timestamp}",
        cnpj=f"{timestamp[:14]}",  # Use timestamp as CNPJ
        email=f"teste{timestamp}@empresa.com",
        phone="11999999999",
        address="Rua Teste, 123",
        is_active=True
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company):
    """Cria um usuário de teste"""
    # Primeiro, precisamos de um role
    from app.models.role import Role
    role = db_session.query(Role).filter(Role.name == "admin").first()
    if not role:
        role = Role(name="admin", description="Administrator")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    
    user = User(
        name="Admin Teste",
        email=f"admin{int(time.time() * 1000)}@teste.com",
        password_hash="hashed",
        role_id=role.id,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_product(db_session, test_company):
    """Cria um produto de teste"""
    product = Product(
        name="Produto Teste",
        description="Descrição teste",
        sale_price=100.0,
        cost_price=50.0,
        stock_quantity=1000,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def customer_without_cpf(db_session, test_company):
    """Cliente SEM CPF (mas com telefone e endereço)"""
    customer = Customer(
        name="Cliente Sem CPF",
        phone="11999999999",
        address="Rua Teste, 123",
        cpf=None,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_without_phone(db_session, test_company):
    """Cliente SEM telefone (mas com CPF e endereço)"""
    customer = Customer(
        name="Cliente Sem Telefone",
        cpf="12345678901",
        address="Rua Teste, 123",
        phone=None,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_without_address(db_session, test_company):
    """Cliente SEM endereço (mas com CPF e telefone)"""
    customer = Customer(
        name="Cliente Sem Endereço",
        cpf="12345678901",
        phone="11999999999",
        address=None,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_incomplete(db_session, test_company):
    """Cliente SEM CPF, telefone e endereço"""
    customer = Customer(
        name="Cliente Incompleto",
        cpf=None,
        phone=None,
        address=None,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_complete(db_session, test_company):
    """Cliente COM todos os dados"""
    customer = Customer(
        name="Cliente Completo",
        cpf="12345678901",
        phone="11999999999",
        address="Rua Teste, 123, Bairro, Cidade - UF",
        email="cliente@teste.com",
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


# ============================================================================
# TESTES: Vendas à Vista (CASH) - Devem ACEITAR clientes sem dados completos
# ============================================================================

def test_cash_sale_with_incomplete_customer(db_session, test_user, test_product, customer_incomplete):
    """
    TDD: Venda à vista (CASH) deve ACEITAR cliente sem CPF, telefone e endereço
    """
    sale_data = SaleCreate(
        customer_id=customer_incomplete.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="cash",
        discount_amount=0
    )
    
    # Não deve lançar exceção
    sale = create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert sale is not None
    assert sale.customer_id == customer_incomplete.id
    assert sale.payment_type == "cash"


# ============================================================================
# TESTES: Vendas PIX - Devem ACEITAR clientes sem dados completos
# ============================================================================

def test_pix_sale_with_incomplete_customer(db_session, test_user, test_product, customer_incomplete):
    """
    TDD: Venda PIX deve ACEITAR cliente sem CPF, telefone e endereço
    """
    sale_data = SaleCreate(
        customer_id=customer_incomplete.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="pix",
        discount_amount=0
    )
    
    # Não deve lançar exceção
    sale = create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert sale is not None
    assert sale.customer_id == customer_incomplete.id
    assert sale.payment_type == "pix"


# ============================================================================
# TESTES: Vendas a Crediário - Devem REJEITAR clientes sem dados completos
# ============================================================================

def test_credit_sale_without_cpf_should_fail(db_session, test_user, test_product, customer_without_cpf):
    """
    TDD: Venda a crediário deve REJEITAR cliente sem CPF
    """
    sale_data = SaleCreate(
        customer_id=customer_without_cpf.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="credit",
        installments_count=3,
        discount_amount=0
    )
    
    # Deve lançar HTTPException
    with pytest.raises(HTTPException) as exc_info:
        create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert exc_info.value.status_code == 400
    assert "CPF" in exc_info.value.detail


def test_credit_sale_without_phone_should_fail(db_session, test_user, test_product, customer_without_phone):
    """
    TDD: Venda a crediário deve REJEITAR cliente sem telefone
    """
    sale_data = SaleCreate(
        customer_id=customer_without_phone.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="credit",
        installments_count=3,
        discount_amount=0
    )
    
    # Deve lançar HTTPException
    with pytest.raises(HTTPException) as exc_info:
        create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert exc_info.value.status_code == 400
    assert "Telefone" in exc_info.value.detail


def test_credit_sale_without_address_should_fail(db_session, test_user, test_product, customer_without_address):
    """
    TDD: Venda a crediário deve REJEITAR cliente sem endereço
    """
    sale_data = SaleCreate(
        customer_id=customer_without_address.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="credit",
        installments_count=3,
        discount_amount=0
    )
    
    # Deve lançar HTTPException
    with pytest.raises(HTTPException) as exc_info:
        create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert exc_info.value.status_code == 400
    assert "Endereço" in exc_info.value.detail


def test_credit_sale_with_complete_customer_should_pass(db_session, test_user, test_product, customer_complete):
    """
    TDD: Venda a crediário deve ACEITAR cliente com todos os dados
    """
    sale_data = SaleCreate(
        customer_id=customer_complete.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=2,
                unit_price=100.0
            )
        ],
        payment_type="credit",
        installments_count=3,
        first_due_date=datetime.now() + timedelta(days=30),
        discount_amount=0
    )
    
    # Não deve lançar exceção
    sale = create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert sale is not None
    assert sale.customer_id == customer_complete.id
    assert sale.payment_type == "credit"
    assert sale.total_amount == 200.0


def test_credit_sale_missing_multiple_fields(db_session, test_user, test_product, customer_incomplete):
    """
    TDD: Venda a crediário deve listar TODOS os campos faltantes na mensagem de erro
    """
    sale_data = SaleCreate(
        customer_id=customer_incomplete.id,
        items=[
            SaleItemIn(
                product_id=test_product.id,
                quantity=1,
                unit_price=100.0
            )
        ],
        payment_type="credit",
        installments_count=3,
        discount_amount=0
    )
    
    # Deve lançar HTTPException
    with pytest.raises(HTTPException) as exc_info:
        create_sale(sale_data, current_user=test_user, db=db_session)
    
    assert exc_info.value.status_code == 400
    # Deve mencionar todos os 3 campos faltantes
    assert "CPF" in exc_info.value.detail
    assert "Telefone" in exc_info.value.detail
    assert "Endereço" in exc_info.value.detail
