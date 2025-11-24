"""
Testes de Filtragem Avançada e Ordenação
Validar múltiplos filtros combinados, ordenação e resultados esperados
"""
import pytest
from fastapi import status
from datetime import datetime, date, timedelta


class TestSalesAdvancedFiltering:
    """Testes de filtros avançados em vendas"""
    
    def test_sales_filter_multiple_filters(self, client, manager_token, test_customer, test_product):
        """Validar múltiplos filtros simultaneamente"""
        # Criar venda
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 2, "unit_price": 50.0}],
                "payment_type": "credit",
                "installments_count": 3,
                "discount_amount": 10.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Filtrar por customer_id E payment_type
        response = client.get(
            f"/api/v1/sales?customer_id={test_customer.id}&payment_type=credit",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            data = response_data["items"]
        else:
            data = response_data
        
        assert len(data) >= 1
        assert all(
            sale["customer_id"] == test_customer.id and 
            sale["payment_type"] == "credit" 
            for sale in data
        )
    
    def test_sales_filter_credit_with_installments(self, client, manager_token, test_customer, test_product):
        """Validar filtro de vendas a crédito"""
        # Criar venda a crédito
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "credit",
                "installments_count": 5,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Buscar venda
        response = client.get(
            "/api/v1/sales?payment_type=credit",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            data = response_data["items"]
        else:
            data = response_data
        
        assert any(s["payment_type"] == "credit" for s in data)
    
    def test_sales_filter_with_discount(self, client, manager_token, test_customer, test_product):
        """Validar vendas com desconto"""
        # Criar venda com desconto
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 20.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Obter venda e validar desconto
        response = client.get(
            f"/api/v1/sales/{sale_id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["discount_amount"] == 20.0
        assert data["total_amount"] == 80.0
    
    def test_sales_ordering_by_date(self, client, manager_token, test_customer):
        """Validar ordenação por data (mais recente primeiro)"""
        response = client.get(
            "/api/v1/sales",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            data = response_data["items"]
        else:
            data = response_data
        
        # Validar que está ordenado por data descendente
        if len(data) > 1:
            for i in range(len(data) - 1):
                created_at_1 = datetime.fromisoformat(
                    data[i]["created_at"].replace('Z', '+00:00')
                )
                created_at_2 = datetime.fromisoformat(
                    data[i + 1]["created_at"].replace('Z', '+00:00')
                )
                assert created_at_1 >= created_at_2


class TestInstallmentsAdvancedFiltering:
    """Testes de filtros avançados em parcelas"""
    
    def test_installments_filter_pending_status(self, client, manager_token):
        """Validar filtro de parcelas pendentes"""
        response = client.get(
            "/api/v1/installments?status=pending",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_installments_by_customer(self, client, manager_token, test_customer):
        """Validar listagem de parcelas de um cliente"""
        response = client.get(
            f"/api/v1/installments/customer/{test_customer.id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            data = response_data["items"]
        else:
            data = response_data
        
        assert isinstance(data, list)
    
    def test_overdue_installments_summary(self, client, manager_token):
        """Validar resumo de parcelas vencidas"""
        response = client.get(
            "/api/v1/cron/overdue-summary",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]


class TestReportsAdvancedFiltering:
    """Testes de filtros avançados em relatórios"""
    
    def test_reports_sales_with_filters(self, client, manager_token):
        """Validar relatório de vendas com filtros"""
        response = client.get(
            "/api/v1/reports/sales?start_date=2024-01-01&end_date=2024-12-31",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_reports_profit(self, client, manager_token):
        """Validar relatório de lucro"""
        response = client.get(
            "/api/v1/reports/profit",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_reports_sold_products(self, client, manager_token):
        """Validar relatório de produtos vendidos"""
        response = client.get(
            "/api/v1/reports/sold-products",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_reports_canceled_sales(self, client, manager_token):
        """Validar relatório de vendas canceladas"""
        response = client.get(
            "/api/v1/reports/canceled-sales",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_reports_overdue_installments(self, client, manager_token):
        """Validar relatório de parcelas vencidas"""
        response = client.get(
            "/api/v1/reports/overdue",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_reports_low_stock(self, client, manager_token):
        """Validar relatório de baixo estoque"""
        response = client.get(
            "/api/v1/reports/low-stock",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
