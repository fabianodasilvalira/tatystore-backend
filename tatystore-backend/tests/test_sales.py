"""
Testes de Vendas e Estoque
"""
import pytest
from tests.conftest import get_auth_headers
from datetime import datetime, timedelta


def test_create_sale_cash_success(client, admin_token, test_product, test_customer, db):
    """
    Teste: Criar venda à vista com débito automático de estoque
    """
    initial_stock = test_product.stock_quantity
    
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 5,
                    "unit_price": 20.00
                }
            ]
        }
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["payment_type"] == "cash"
    assert data["total_amount"] == 100.00
    assert data["status"] == "completed"
    
    # Verificar débito de estoque
    db.refresh(test_product)
    assert test_product.stock_quantity == initial_stock - 5


def test_create_sale_credit_with_installments(client, admin_token, test_product, test_customer):
    """
    Teste: Criar venda a crédito com geração de parcelas
    """
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 3,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 2,
                    "unit_price": 20.00
                }
            ]
        }
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["payment_type"] == "credit"
    assert data["total_amount"] == 40.00
    assert len(data["installments"]) == 3
    
    # Verificar valores das parcelas
    for installment in data["installments"]:
        assert abs(installment["amount"] - 40.00 / 3) < 0.01


def test_sale_insufficient_stock(client, admin_token, test_product, test_customer, db):
    """
    Teste: Venda não pode exceder estoque disponível
    """
    test_product.stock_quantity = 3
    db.commit()
    
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 10,
                    "unit_price": 20.00
                }
            ]
        }
    )
    
    assert response.status_code == 400
    assert "estoque insuficiente" in response.json()["detail"].lower()


def test_cancel_sale_restores_stock(client, admin_token, test_product, test_customer, db):
    """
    Usando get_auth_headers para passar token
    Teste: Cancelar venda restaura estoque
    """
    initial_stock = test_product.stock_quantity
    
    # Criar venda
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 3,
                    "unit_price": 20.00
                }
            ]
        }
    )
    
    response_data = response.json()
    sale_id = response_data.get("id")
    if not sale_id:
        # Fallback: buscar venda mais recente do banco
        from app.models.sale import Sale
        sale = db.query(Sale).order_by(Sale.id.desc()).first()
        assert sale is not None, "Sale not created"
        sale_id = sale.id
    
    # Cancelar venda
    response = client.post(
        f"/api/v1/sales/{sale_id}/cancel",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    
    # Verificar restauração de estoque
    db.refresh(test_product)
    assert test_product.stock_quantity == initial_stock


def test_sale_with_discount(client, admin_token, test_product, test_customer):
    """
    Usando get_auth_headers
    Teste: Venda com desconto
    """
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 10.00,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["total_amount"] == 90.00


def test_cannot_access_sale_from_other_company(client, admin_token, company2_token, test_product, test_customer, db):
    """
    Usando get_auth_headers
    Teste: Não pode acessar venda de outra empresa
    """
    # Criar venda com admin da empresa 1
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ]
        }
    )
    
    response_data = response.json()
    sale_id = response_data.get("id")
    if not sale_id:
        # Fallback: buscar venda mais recente do banco
        from app.models.sale import Sale
        sale = db.query(Sale).order_by(Sale.id.desc()).first()
        assert sale is not None, "Sale not created"
        sale_id = sale.id
    
    # Tentar acessar com admin da empresa 2
    response = client.get(
        f"/api/v1/sales/{sale_id}",
        headers=get_auth_headers(company2_token)
    )
    
    assert response.status_code in [404, 403]
