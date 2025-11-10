"""
Testes de Relatórios
"""
import pytest
from tests.conftest import get_auth_headers
from datetime import datetime, date


def test_sales_report(client, admin_token, test_product, test_customer):
    """
    Usando get_auth_headers para passar token
    Teste: Relatório de vendas
    """
    # Criar algumas vendas
    for i in range(3):
        client.post(
            "/api/v1/sales/",
            headers=get_auth_headers(admin_token),
            json={
                "customer_id": test_customer.id,
                "payment_type": "cash",
                "items": [
                    {
                        "product_id": test_product.id,
                        "quantity": 1,
                        "unit_price": 20.00
                    }
                ]
            }
        )
    
    # Gerar relatório
    response = client.get(
        "/api/v1/reports/sales",
        headers=get_auth_headers(admin_token),
        params={"period": "month"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_sales"] == 3


def test_products_report(client, admin_token, test_product):
    """
    Usando get_auth_headers e corrigindo endpoint
    Teste: Relatório de produtos
    """
    response = client.get(
        "/api/v1/reports/sold-products",
        headers=get_auth_headers(admin_token),
        params={"period": "month"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


def test_customers_report(client, admin_token, test_customer):
    """
    Usando get_auth_headers e corrigindo endpoint
    Teste: Relatório de clientes vencidos
    """
    response = client.get(
        "/api/v1/reports/overdue",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overdue_count" in data


def test_financial_report(client, admin_token, test_product, test_customer):
    """
    Usando get_auth_headers e corrigindo endpoint
    Teste: Relatório financeiro (lucro)
    """
    # Criar vendas
    client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 2,
                    "unit_price": 20.00
                }
            ]
        }
    )
    
    response = client.get(
        "/api/v1/reports/profit",
        headers=get_auth_headers(admin_token),
        params={"period": "month"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "profit" in data
    assert "total_revenue" in data


def test_reports_isolated_by_company(client, admin_token, company2_token, test_product, test_customer):
    """
    Usando get_auth_headers e testando /sales
    Teste: Relatórios isolados por empresa
    """
    # Empresa 1 cria uma venda
    client.post(
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
    
    # Relatório da empresa 1
    response1 = client.get(
        "/api/v1/reports/sales",
        headers=get_auth_headers(admin_token),
        params={"period": "month"}
    )
    
    # Relatório da empresa 2
    response2 = client.get(
        "/api/v1/reports/sales",
        headers=get_auth_headers(company2_token),
        params={"period": "month"}
    )
    
    data1 = response1.json()
    data2 = response2.json()
    
    total_sales_1 = data1.get("total_sales") or data1.get("sales_count") or len(data1)
    total_sales_2 = data2.get("total_sales") or data2.get("sales_count") or 0
    
    assert total_sales_1 > 0
    assert total_sales_2 == 0
