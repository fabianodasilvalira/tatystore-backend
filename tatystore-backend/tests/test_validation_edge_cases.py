"""
Testes de Validações e Edge Cases (Fase 5)
Validação de entrada, formatos, limites e comportamentos extremos
"""
import pytest
from fastapi import status


class TestEmailValidation:
    """Testes de validação de email"""
    
    def test_duplicate_user_email_rejected(self, client, admin_token, test_admin_user, test_roles):
        """Dois usuários não podem ter mesmo email"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Outro Admin",
            "email": "admin@teste.com",  # Email já existe
            "password": "OtherPass123!",
            "role_id": test_roles["admin"].id
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_email_case_insensitive_duplicate_check(self, client, admin_token, test_admin_user, test_roles):
        """Email check deve ser case-insensitive"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Case Test",
            "email": "ADMIN@TESTE.COM",  # Mesmo email, caso diferente
            "password": "CasePass123!",
            "role_id": test_roles["admin"].id
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]


class TestCNPJValidation:
    """Testes de validação de CNPJ"""
    
    def test_duplicate_cnpj_rejected(self, client, test_company1, db):
        """Duas empresas não podem ter mesmo CNPJ"""
        # Criar Super Admin para o teste
        from app.models.role import Role
        from app.models.user import User
        from app.core.security import get_password_hash

        sa_role = Role(name="Super Admin", description="God mode")
        db.add(sa_role)
        db.commit()
        db.refresh(sa_role)

        sa_user = User(
            name="Super",
            email="super@test.com",
            password_hash=get_password_hash("123"),
            role_id=sa_role.id,
            is_active=True
        )
        db.add(sa_user)
        db.commit()

        # Login para pegar token
        login_resp = client.post("/api/v1/auth/login", json={"email": "super@test.com", "password": "123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        company_data = {
            "name": "Empresa Duplicada",
            "cnpj": test_company1.cnpj,
            "email": "duplicada@empresa.com",
            "phone": "11111111111"
        }
        
        response = client.post(
            "/api/v1/companies/",
            json=company_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestStockValidation:
    """Testes de validação de estoque"""
    
    def test_negative_stock_prevention(self, client, manager_token, test_customer, test_product, db):
        """Não deve vender quantidade maior que estoque"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Tentar vender mais que o estoque
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 10000,  # Muito mais que os 100 de estoque
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDiscountValidation:
    """Testes de validação de desconto"""
    
    def test_negative_discount_rejected(self, client, manager_token, test_customer, test_product):
        """Desconto negativo deve ser rejeitado"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": -10.00,  # Negativo
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
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestInstallmentValidation:
    """Testes de validação de parcelamento"""
    
    def test_installments_between_1_and_60(self, client, manager_token, test_customer, test_product):
        """Parcelas deve estar entre 1 e 60"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        # Testar 61 parcelas
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 61,
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
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
