"""
Testes de Produtos
"""
import pytest
from tests.conftest import get_auth_headers


def test_create_product_success(client, admin_token):
    """
    Usando get_auth_headers para passar token
    Teste: Criar produto com dados válidos
    """
    response = client.post(
        "/api/v1/products/",
        headers=get_auth_headers(admin_token),
        json={
            "name": "Produto Novo",
            "sku": "PROD-999",
            "cost_price": 50.00,
            "sale_price": 100.00,
            "stock_quantity": 20
        }
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Produto Novo"
    assert data["stock_quantity"] == 20


def test_list_products_own_company_only(client, admin_token, company2_token, test_product, test_product_company2):
    """
    Usando get_auth_headers para ambas empresas
    Teste: Usuário só vê produtos da própria empresa
    """
    # Empresa 1 deve ver apenas produto 1
    response = client.get(
        "/api/v1/products/",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    product_ids = [p["id"] for p in data]
    assert test_product.id in product_ids
    assert test_product_company2.id not in product_ids
    
    # Empresa 2 deve ver apenas produto 2
    response = client.get(
        "/api/v1/products/",
        headers=get_auth_headers(company2_token)
    )
    
    data = response.json()
    product_ids = [p["id"] for p in data]
    assert test_product_company2.id in product_ids
    assert test_product.id not in product_ids


def test_cannot_access_product_from_other_company(client, admin_token, test_product_company2):
    """
    Usando get_auth_headers
    Teste: Não pode acessar produto de outra empresa
    """
    response = client.get(
        f"/api/v1/products/{test_product_company2.id}",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 404


def test_update_product_reduces_stock(client, admin_token, test_product):
    """
    Usando get_auth_headers
    Teste: Atualizar quantidade de estoque
    """
    response = client.put(
        f"/api/v1/products/{test_product.id}",
        headers=get_auth_headers(admin_token),
        json={"stock_quantity": 50}
    )
    
    assert response.status_code == 200
    assert response.json()["stock_quantity"] == 50


def test_low_stock_alert(client, admin_token, db, test_product):
    """
    Usando get_auth_headers
    Teste: Produto com estoque baixo deve ser sinalizado
    """
    # Reduzir estoque abaixo do mínimo
    test_product.stock_quantity = 5
    db.commit()
    
    response = client.get(
        "/api/v1/products/low-stock",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(p["id"] == test_product.id for p in data)
