"""
Testes avançados de permissões e roles
Cobertura: Controle de acesso granular por role
"""
import pytest
from fastapi import status


class TestRolePermissions:
    """Testes de permissões específicas por role"""
    
    def test_admin_full_access(self, client, admin_token, test_product):
        """Admin deve ter acesso total a todos os endpoints"""
        # Listar produtos
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Criar produto
        response = client.post(
            "/api/v1/products",
            json={
                "name": "Novo Produto",
                "cost_price": 10.0,
                "sale_price": 20.0,
                "stock_quantity": 100,
                "min_stock": 10
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Deletar produto
        response = client.delete(
            f"/api/v1/products/{test_product.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_manager_intermediate_access(self, client, manager_token, test_product):
        """Gerente deve ter acesso intermediário"""
        # Pode listar produtos
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Pode criar produto
        response = client.post(
            "/api/v1/products",
            json={
                "name": "Produto Gerente",
                "cost_price": 10.0,
                "sale_price": 20.0,
                "stock_quantity": 50,
                "min_stock": 5
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_seller_limited_access(self, client, seller_token, test_product):
        """Vendedor deve ter acesso limitado"""
        # Pode listar produtos
        response = client.get(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Não pode deletar produtos
        response = client.delete(
            f"/api/v1/products/{test_product.id}",
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]
    
    def test_seller_cannot_create_users(self, client, seller_token):
        """Vendedor não pode criar usuários"""
        response = client.post(
            "/api/v1/users",
            json={
                "name": "Novo Usuario",
                "email": "novo@teste.com",
                "password": "Senha@123",
                "role_id": 1
            },
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manager_can_create_users(self, client, manager_token, db):
        """Gerente pode criar usuários"""
        from app.models.role import Role
        
        role = db.query(Role).first()
        
        response = client.post(
            "/api/v1/users",
            json={
                "name": "Usuario Gerente",
                "email": "gerente.user@teste.com",
                "password": "Senha@123",
                "role_id": role.id
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]


class TestCrossCompanyPermissions:
    """Testes de isolamento entre empresas"""
    
    def test_cannot_update_other_company_product(self, client, admin_token, test_product2):
        """Usuário de empresa A não pode atualizar produto da empresa B"""
        response = client.put(
            f"/api/v1/products/{test_product2.id}",
            json={"name": "Tentativa de Hack"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Sistema retorna 403 quando tenta acessar recurso de outra empresa
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_cannot_view_other_company_customers(self, client, admin_token, test_customer2):
        """Não deve ver clientes de outra empresa"""
        response = client.get(
            f"/api/v1/customers/{test_customer2.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cannot_create_sale_for_other_company_customer(self, client, admin_token, test_customer2, test_product):
        """Não pode criar venda para cliente de outra empresa"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer2.id,
                "payment_type": "cash",
                "items": [
                    {"product_id": test_product.id, "quantity": 1}
                ]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Pode retornar 422 por validação ou 404/400 por não encontrar recurso
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestSpecialScenarios:
    """Cenários especiais de permissões"""
    
    def test_inactive_user_blocked_from_all_endpoints(self, client, db, test_company1, test_roles):
        """Usuário inativo não pode acessar nenhum endpoint"""
        # Criar usuário inativo
        from app.models.user import User
        from app.core.security import get_password_hash
        
        inactive_user = User(
            name="Usuario Inativo",
            email="inativo@teste.com",
            password_hash=get_password_hash("inativo123"),
            company_id=test_company1.id,
            role_id=test_roles["admin"].id,
            is_active=False
        )
        db.add(inactive_user)
        db.commit()
        
        # Tentar fazer login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "inativo@teste.com", "password": "inativo123"}
        )
        
        # Sistema pode retornar 403 ou 401 dependendo da implementação
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_user_from_inactive_company_blocked(self, client, db, test_roles):
        """Usuário de empresa inativa não pode fazer login"""
        # Criar empresa inativa
        from app.models.company import Company
        from app.models.user import User
        from app.core.security import get_password_hash
        
        inactive_company = Company(
            name="Empresa Inativa",
            slug="empresa-inativa",
            cnpj="99999999000199",
            email="inativa@teste.com",
            phone="11777777777",
            is_active=False
        )
        db.add(inactive_company)
        db.commit()
        
        user = User(
            name="Usuario Empresa Inativa",
            email="user.inativa@teste.com",
            password_hash=get_password_hash("senha123"),
            company_id=inactive_company.id,
            role_id=test_roles["admin"].id,
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Tentar fazer login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user.inativa@teste.com", "password": "senha123"}
        )
        
        # Sistema pode retornar 403 ou 401 dependendo da implementação
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
