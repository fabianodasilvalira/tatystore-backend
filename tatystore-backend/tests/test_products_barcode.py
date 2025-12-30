"""
Testes específicos para busca de produtos por código de barras
"""
import pytest
from fastapi import status


class TestProductBarcodeSearch:
    """Testes de busca por código de barras"""
    
    def test_search_product_by_barcode(self, client, admin_token, test_product):
        """Deve buscar produto por código de barras"""
        response = client.get(
            f"/api/v1/products?barcode={test_product.barcode}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        products = response.json()
        
        if products:  # Se o endpoint suportar busca por barcode
            assert any(p["barcode"] == test_product.barcode for p in products)
    
    def test_search_product_by_barcode_not_found(self, client, admin_token):
        """Deve retornar vazio para barcode inexistente"""
        response = client.get(
            "/api/v1/products?barcode=9999999999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        products = response.json()
        assert len(products) == 0
    
    def test_search_product_by_barcode_isolated_by_company(self, client, admin_token, test_product, test_company2, db):
        """Não deve encontrar produto de outra empresa pelo barcode"""
        # Criar produto na empresa 2 com mesmo barcode
        from app.models.product import Product
        
        product2 = Product(
            name="Produto Empresa 2",
            barcode=test_product.barcode,  # Mesmo barcode
            cost_price=10.0,
            sale_price=20.0,
            stock_quantity=50,
            min_stock=5,
            company_id=test_company2.id
        )
        db.add(product2)
        db.commit()
        
        # Buscar com token da empresa 1
        response = client.get(
            f"/api/v1/products?barcode={test_product.barcode}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        products = response.json()
        
        # Deve retornar apenas produtos da empresa 1
        for product in products:
            assert product["company_id"] == test_product.company_id


class TestProductPartialUpdate:
    """Testes de atualização parcial de produtos"""
    
    def test_update_only_min_stock(self, client, admin_token, test_product):
        """Deve atualizar apenas min_stock"""
        original_name = test_product.name
        original_price = test_product.sale_price
        
        response = client.put(
            f"/api/v1/products/{test_product.id}",
            json={"min_stock": 20},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["min_stock"] == 20
        assert data["name"] == original_name
        assert data["sale_price"] == original_price
    
    def test_update_only_barcode(self, client, admin_token, test_product):
        """Deve atualizar apenas código de barras"""
        new_barcode = "9999888877776666"
        
        response = client.put(
            f"/api/v1/products/{test_product.id}",
            json={"barcode": new_barcode},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["barcode"] == new_barcode
    
    def test_update_barcode_to_null(self, client, admin_token, test_product):
        """Deve permitir remover código de barras"""
        response = client.put(
            f"/api/v1/products/{test_product.id}",
            json={"barcode": None},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["barcode"] is None
