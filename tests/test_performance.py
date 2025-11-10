"""
Testes de Performance e Carga
Validar tempo de resposta e comportamento sob carga
"""
import pytest
from fastapi import status
import time


class TestResponseTimeSales:
    """Testes de tempo de resposta para vendas"""
    
    def test_create_sale_response_time(self, client, manager_token, test_customer, test_product):
        """Validar que criar venda é rápido (< 1 segundo)"""
        start_time = time.time()
        
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
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_201_CREATED
        assert elapsed_time < 1.0, f"Tempo de resposta muito longo: {elapsed_time}s"
    
    def test_list_sales_response_time(self, client, manager_token):
        """Validar que listar vendas é rápido (< 2 segundos)"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/sales?skip=0&limit=100",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 2.0, f"Tempo de resposta muito longo: {elapsed_time}s"
    
    def test_get_sale_details_response_time(self, client, manager_token, test_customer, test_product):
        """Validar que obter detalhes de venda é rápido (< 500ms)"""
        # Criar venda primeiro
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
        sale_id = response.json()["id"]
        
        # Medir tempo de busca
        start_time = time.time()
        response = client.get(
            f"/api/v1/sales/{sale_id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 0.5, f"Tempo de resposta muito longo: {elapsed_time}s"


class TestResponseTimeCustomers:
    """Testes de tempo de resposta para clientes"""
    
    def test_list_customers_response_time(self, client, manager_token):
        """Validar que listar clientes é rápido (< 1 segundo)"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/customers?skip=0&limit=100",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 1.0, f"Tempo de resposta muito longo: {elapsed_time}s"


class TestLoadHandling:
    """Testes de comportamento sob carga"""
    
    def test_multiple_sequential_list_requests(self, client, manager_token):
        """Validar que múltiplas requisições sequenciais são tratadas"""
        for _ in range(10):
            response = client.get(
                "/api/v1/sales?skip=0&limit=50",
                headers={"Authorization": f"Bearer {manager_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
    
    def test_multiple_sequential_create_requests(self, client, manager_token, test_customer, test_product):
        """Validar que múltiplas criações sequenciais são tratadas"""
        successful_count = 0
        for _ in range(5):
            response = client.post(
                "/api/v1/sales",
                json={
                    "customer_id": test_customer.id,
                    "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 50.0}],
                    "payment_type": "cash",
                    "discount_amount": 0.0
                },
                headers={"Authorization": f"Bearer {manager_token}"}
            )
            if response.status_code == status.HTTP_201_CREATED:
                successful_count += 1
        
        assert successful_count >= 4, "A maioria das requisições devem ser bem-sucedidas"


class TestQueryPerformance:
    """Testes de performance de queries"""
    
    def test_list_sales_with_large_limit(self, client, manager_token):
        """Validar que queries com large limit são tratadas eficientemente"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/sales?skip=0&limit=1000",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        # Deve ser rápido mesmo com limite alto
        assert elapsed_time < 5.0, f"Query muito lenta com limite alto: {elapsed_time}s"
    
    def test_reports_generation_performance(self, client, manager_token):
        """Validar que geração de relatórios é rápida"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/reports/sales",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 3.0, f"Relatório muito lento: {elapsed_time}s"
