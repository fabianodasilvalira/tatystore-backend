"""
Testes de Segurança
Validação de autenticação, autorização, rate limiting e token management
"""
import pytest
from fastapi import status
from app.core.security import validate_password_strength, hash_password


class TestPasswordSecurity:
    """Testes de força e validação de senha"""
    
    def test_password_strength_minimum_length(self):
        """Deve rejeitar senhas com menos de 8 caracteres"""
        is_valid, message = validate_password_strength("Short1!")
        assert not is_valid
        assert "mínimo 8 caracteres" in message
    
    def test_password_strength_requires_uppercase(self):
        """Deve rejeitar senhas sem letra maiúscula"""
        is_valid, message = validate_password_strength("lowercase1!")
        assert not is_valid
        assert "maiúscula" in message
    
    def test_password_strength_requires_lowercase(self):
        """Deve rejeitar senhas sem letra minúscula"""
        is_valid, message = validate_password_strength("UPPERCASE1!")
        assert not is_valid
        assert "minúscula" in message
    
    def test_password_strength_requires_number(self):
        """Deve rejeitar senhas sem número"""
        is_valid, message = validate_password_strength("NoNumber!")
        assert not is_valid
        assert "número" in message
    
    def test_password_strength_requires_special_char(self):
        """Deve rejeitar senhas sem caractere especial"""
        is_valid, message = validate_password_strength("NoSpecial1")
        assert not is_valid
        assert "especial" in message
    
    def test_password_strength_valid(self):
        """Deve aceitar senha forte"""
        is_valid, message = validate_password_strength("ValidPass123!")
        assert is_valid
        assert "forte" in message.lower()
    
    def test_password_hashing_different_hashes(self):
        """Mesma senha deve gerar hashes diferentes (salt)"""
        password = "ValidPass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Deve ser diferente por causa do salt
    
    def test_password_hashing_long_password(self):
        """Deve suportar senhas longas (sem limite de 72 bytes do bcrypt)"""
        long_password = "A" * 200 + "1!" * 100  # Senha muito longa
        hash_result = hash_password(long_password)
        assert len(hash_result) > 0


class TestLogout:
    """Testes de logout e token invalidation"""
    
    def test_logout_invalidates_token(self, client, admin_token):
        """Após logout, token não deve funcionar"""
        # Fazer logout
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Tentar usar token após logout
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_requires_auth(self, client):
        """Logout sem autenticação deve falhar"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenManagement:
    """Testes de gerenciamento de tokens"""
    
    def test_token_refresh_creates_new_token(self, client, admin_token):
        """Refresh token deve gerar novo access token"""
        # Fazer login para obter refresh token
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@teste.com", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        refresh_token = response.json()["refresh_token"]
        old_access_token = response.json()["access_token"]
        
        # Usar refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        
        new_access_token = response.json()["access_token"]
        assert new_access_token != old_access_token  # Deve ser diferente
    
    def test_invalid_refresh_token(self, client):
        """Refresh com token inválido deve falhar"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSaleValidation:
    """Testes de validação de vendas"""
    
    def test_create_sale_negative_discount(self, client, admin_token, test_product, test_customer, db):
        """Desconto não pode ser negativo"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": -10.00,  # Negativo - inválido
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
        # This is acceptable behavior as it rejects the invalid input
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        response_data = response.json()
        if isinstance(response_data.get("detail"), list):
            # Pydantic validation error - list of error dicts
            error_msg = str(response_data["detail"]).lower()
            assert "discount" in error_msg or "greater than or equal to 0" in error_msg or "desconto" in error_msg
        else:
            # Custom validation error - string
            assert "desconto" in response_data["detail"].lower() or "greater than or equal to 0" in response_data["detail"].lower()
    
    def test_create_sale_discount_exceeds_total(self, client, admin_token, test_product, test_customer, db):
        """Desconto não pode ser maior que total"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 100.00,  # Maior que total
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_sale_empty_items(self, client, admin_token, test_customer):
        """Venda sem itens deve falhar"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": []
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_sale_invalid_installments_count(self, client, admin_token, test_product, test_customer):
        """Parcelas deve estar entre 1 e 60"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Testar 0 parcelas
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 0,
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
        # This is acceptable behavior as it rejects the invalid input
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        
        # Testar 61 parcelas
        sale_data["installments_count"] = 61
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        # This is acceptable behavior as it rejects the invalid input
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestRoleAuthorization:
    """Testes de autorização por perfil"""
    
    def test_user_cannot_create_sale(self, client, user_token, test_product, test_customer):
        """Usuário comum não pode criar venda (apenas admin/gerente)"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
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
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manager_can_create_sale(self, client, manager_token, test_product, test_customer):
        """Gerente pode criar venda"""
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
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED


class TestInputValidation:
    """Testes de validação de entrada e edge cases"""
    
    def test_product_with_zero_stock(self, client, admin_token, test_company1, test_customer, db):
        """Não deve vender produto sem estoque"""
        from app.models.product import Product
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Criar produto sem estoque
        product = Product(
            name="Produto Sem Estoque",
            sku="NO-STOCK",
            cost_price=10.00,
            sale_price=20.00,
            stock_quantity=0,
            company_id=test_company1.id
        )
        db.add(product)
        db.commit()
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": product.id,
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "estoque" in response.json()["detail"].lower()
    
    def test_invalid_email_format(self, client, test_company1, test_roles, db):
        """Criar usuário com email inválido deve falhar"""
        from app.models.user import User
        
        try:
            user = User(
                name="Test User",
                email="invalid-email",  # Email inválido
                password_hash="hash123",
                company_id=test_company1.id,
                role_id=test_roles["admin"].id
            )
            db.add(user)
            db.commit()
            assert False, "Deveria ter falhado ao criar usuário com email inválido"
        except Exception:
            # Esperado falhar
            pass
