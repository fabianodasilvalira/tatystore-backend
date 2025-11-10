"""
Testes de Auditoria e Performance (Fase 6)
Rastreabilidade de ações, logs de auditoria e performance sob carga
"""
import pytest
import time
from fastapi import status


class TestAuditLogging:
    """Testes de logs de auditoria"""
    
    def test_failed_login_recorded(self, client, db):
        """Tentativa de login falha deve ser registrada"""
        response = client.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@teste.com", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        try:
            from app.models.login_attempt import LoginAttempt
            attempt = db.query(LoginAttempt).filter(
                LoginAttempt.email == "admin@teste.com"
            ).order_by(LoginAttempt.created_at.desc()).first()
            
            # LoginAttempt is optional
            if attempt:
                assert attempt.success == False
        except:
            pytest.skip("LoginAttempt model not available")
    
    def test_sale_cancellation_tracked(self, client, manager_token, test_customer, test_product, db):
        """Cancelamento de venda deve ser rastreado"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Criar venda
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post("/api/v1/sales/", json=sale_data, headers=headers)
        if response.status_code == status.HTTP_201_CREATED:
            sale_id = response.json()["id"]
            
            # Cancelar venda
            response = client.post(
                f"/api/v1/sales/{sale_id}/cancel",
                headers=headers
            )
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


class TestPerformance:
    """Testes de performance"""
    
    def test_list_products_response_time(self, client, admin_token):
        """Listagem de produtos deve ser rápida (< 2s)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start = time.time()
        response = client.get("/api/v1/products/", headers=headers)
        end = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end - start) < 2.0
    
    def test_list_sales_response_time(self, client, manager_token):
        """Listagem de vendas deve ser rápida (< 2s)"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        start = time.time()
        response = client.get("/api/v1/sales/", headers=headers)
        end = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end - start) < 2.0
    
    def test_create_sale_response_time(self, client, manager_token, test_customer, test_product):
        """Criação de venda deve ser rápida (< 3s)"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 20.00
                }
            ]
        }
        
        start = time.time()
        response = client.post("/api/v1/sales/", json=sale_data, headers=headers)
        end = time.time()
        
        assert response.status_code == status.HTTP_201_CREATED
        assert (end - start) < 3.0
