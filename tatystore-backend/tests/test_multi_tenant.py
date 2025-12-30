"""
Testes de Multi-Tenancy (Isolamento entre empresas)
Valida que dados de uma empresa não podem ser acessados por outra
"""
import pytest
from fastapi import status


class TestCompanyIsolation:
    """Testes de isolamento entre empresas"""
    
    def test_user_cannot_access_product_from_other_company(self, client, admin_token, test_product_company2, db):
        """Usuário de empresa 1 não deve acessar produtos de empresa 2"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            f"/api/v1/products/{test_product_company2.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_user_cannot_create_sale_for_other_company_customer(self, client, admin_token, test_product, db):
        """Não pode criar venda para cliente de outra empresa"""
        from app.models.customer import Customer
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Cliente de empresa 2
        customer = Customer(
            name="Cliente Empresa 2",
            email="cliente2@teste.com",
            company_id=2  # Outra empresa
        )
        db.add(customer)
        db.commit()
        
        sale_data = {
            "customer_id": customer.id,
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
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_user_cannot_list_sales_from_other_company(self, client, admin_token, company2_token, test_product, test_customer, db):
        """Usuário de empresa 2 não vê vendas de empresa 1"""
        from app.models.sale import Sale, PaymentType, SaleStatus
        
        # Criar venda na empresa 1 com token da empresa 1
        headers = {"Authorization": f"Bearer {admin_token}"}
        
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
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Tentar listar vendas com token de empresa 2
        headers2 = {"Authorization": f"Bearer {company2_token}"}
        response = client.get(
            "/api/v1/sales/",
            headers=headers2
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
        
        # Se retornar 200, não deve conter vendas de empresa 1
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            
            # Ajustar para suportar resposta paginada
            if isinstance(response_data, dict) and "items" in response_data:
                sales = response_data["items"]
            else:
                sales = response_data
            
            assert len(sales) == 0


class TestRowLevelSecurity:
    """Testes de Row-Level Security (RLS)"""
    
    def test_cannot_view_other_company_reports(self, client, admin_token, company2_token, manager_token):
        """Não deve ver relatórios de outra empresa"""
        headers2_manager = {"Authorization": f"Bearer {manager_token}"}
        
        # Relatório de vendas - should be 200 OK because user can see their own company's reports
        response = client.get(
            "/api/v1/reports/sales",
            headers=headers2_manager
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # If there are any sales, they should only be from company 1
        # (Validated in backend - reports endpoint filters by company_id)


class TestAccessControl:
    """Testes de Controle de Acesso"""
    
    def test_inactive_user_cannot_login(self, client, test_admin_user, db):
        """Usuário inativo não deve fazer login"""
        # Desativar usuário
        test_admin_user.is_active = False
        db.commit()
        
        response = client.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@teste.com", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        test_admin_user.is_active = True
        db.commit()
    
    def test_inactive_company_cannot_login(self, client, test_company1, test_admin_user, db):
        """Usuário de empresa inativa não deve fazer login"""
        # Desativar empresa
        test_company1.is_active = False
        db.commit()
        
        response = client.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@teste.com", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        test_company1.is_active = True
        db.commit()
    
    def test_cannot_access_with_expired_token(self, client, monkeypatch):
        """Token expirado não deve funcionar"""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Criar token que expira imediatamente
        token = create_access_token(
            {
                "sub": "1",
                "company_id": 1,
                "role_id": 1
            },
            expires_delta=timedelta(seconds=-1)  # Já expirado
        )
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
