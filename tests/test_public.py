"""
Testes de Rotas Públicas
"""
import pytest


def test_list_products_public_no_auth(client, test_product, test_company1):
    """
    Teste: Visitantes podem ver produtos sem autenticação
    """
    response = client.get(f"/api/v1/public/companies/{test_company1.slug}/products")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    product = data[0]
    assert "sale_price" in product
    assert "cost_price" not in product


def test_get_product_detail_public(client, test_product, test_company1):
    """
    Teste: Detalhes de produto público
    """
    response = client.get(
        f"/api/v1/public/companies/{test_company1.slug}/products/{test_product.id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_product.name
    assert "cost_price" not in data


def test_public_route_company_isolation(client, test_product, test_product_company2, test_company1, test_company2):
    """
    Teste: Rotas públicas respeitam isolamento de empresa
    """
    response = client.get(f"/api/v1/public/companies/{test_company1.slug}/products")
    data = response.json()
    product_ids = [p["id"] for p in data]
    
    assert test_product.id in product_ids
    assert test_product_company2.id not in product_ids
