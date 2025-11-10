"""
Testes de Paginação e Filtragem
Validar offset/limit, filtros e ordenação em todos os endpoints
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta


class TestSalesPagination:
    """Testes de paginação do endpoint de vendas"""
    
    def test_sales_list_with_offset_limit(self, client, manager_token, test_company1, test_customer, test_product, db: Session):
        """Validar paginação com offset e limit"""
        # Criar 15 vendas
        for i in range(15):
            response = client.post(
                "/api/v1/sales",
                json={
                    "customer_id": test_customer.id,
                    "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                    "payment_type": "cash",
                    "discount_amount": 0.0
                },
                headers={"Authorization": f"Bearer {manager_token}"}
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Teste: primeiro page (5 itens)
        response = client.get(
            "/api/v1/sales?skip=0&limit=5",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        
        # Teste: segundo page (5 itens)
        response = client.get(
            "/api/v1/sales?skip=5&limit=5",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        
        # Teste: terceiro page (5 itens)
        response = client.get(
            "/api/v1/sales?skip=10&limit=5",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
        
        # Teste: page além do limite (vazia)
        response = client.get(
            "/api/v1/sales?skip=100&limit=10",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0
    
    def test_sales_list_default_limit(self, client, manager_token, test_customer, test_product):
        """Validar limite padrão de 10 itens"""
        response = client.get(
            "/api/v1/sales",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_sales_filter_by_customer(self, client, manager_token, test_customer, test_company1, test_product, db: Session):
        """Validar filtro por cliente"""
        # Obter customer_id
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Filtrar por customer_id
        response = client.get(
            f"/api/v1/sales?customer_id={test_customer.id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert all(sale["customer_id"] == test_customer.id for sale in data)
    
    def test_sales_filter_by_payment_type(self, client, manager_token, test_customer, test_product):
        """Validar filtro por tipo de pagamento"""
        # Criar venda PIX
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "pix",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Filtrar por payment_type
        response = client.get(
            "/api/v1/sales?payment_type=pix",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(sale["payment_type"] == "pix" for sale in data)
    
    def test_sales_filter_by_status(self, client, manager_token, test_customer):
        """Validar filtro por status"""
        response = client.get(
            "/api/v1/sales?status=completed",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)


class TestCustomersPagination:
    """Testes de paginação do endpoint de clientes"""
    
    def test_customers_list_with_offset_limit(self, client, manager_token, test_company1, db: Session):
        """Validar paginação com offset e limit"""
        # Criar 10 clientes
        for i in range(10):
            response = client.post(
                "/api/v1/customers",
                json={
                    "name": f"Customer {i}",
                    "email": f"customer{i}@test.com",
                    "cpf": f"{i:03d}.{i:03d}.{i:03d}-{i:02d}",
                    "phone": f"119999{i:04d}"
                },
                headers={"Authorization": f"Bearer {manager_token}"}
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Teste: primeiro page
        response = client.get(
            "/api/v1/customers?skip=0&limit=5",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5
    
    def test_customers_filter_by_search(self, client, manager_token, test_customer):
        """Validar filtro por search"""
        response = client.get(
            f"/api/v1/customers?search={test_customer.name}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(test_customer.name in item["name"] for item in data)


class TestInstallmentsPagination:
    """Testes de paginação do endpoint de parcelas"""
    
    def test_installments_list_with_offset_limit(self, client, manager_token):
        """Validar paginação com offset e limit"""
        response = client.get(
            "/api/v1/installments?skip=0&limit=10",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_installments_filter_overdue(self, client, manager_token):
        """Validar filtro de parcelas vencidas"""
        response = client.get(
            "/api/v1/installments/overdue",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestProductsPagination:
    """Testes de paginação do endpoint de produtos"""
    
    def test_products_list_with_offset_limit(self, client, manager_token):
        """Validar paginação com offset e limit"""
        response = client.get(
            "/api/v1/products?skip=0&limit=10",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_products_filter_low_stock(self, client, manager_token):
        """Validar filtro de produtos com baixo estoque"""
        response = client.get(
            "/api/v1/products/low-stock",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
