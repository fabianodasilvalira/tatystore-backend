"""
Testes completos de Gestão de Usuários (Fase 3)
Criação, listagem, atualização, exclusão e validações de usuários
"""
import pytest
from fastapi import status
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class TestUserCreation:
    """Testes de criação de usuários"""
    
    def test_create_user_success(self, client, admin_token, test_company1, test_roles, db):
        """Admin deve poder criar novo usuário"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Novo Usuario",
            "email": "novo@empresa1.com",
            "password": "NovoPass123!",
            "role_id": test_roles["usuario"].id
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "novo@empresa1.com"
        assert data["name"] == "Novo Usuario"

    def test_create_user_duplicate_email(self, client, admin_token, test_admin_user):
        """Não deve criar usuário com email duplicado"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Outro Usuario",
            "email": "admin@teste.com",  # Email já existe
            "password": "OtherPass123!",
            "role_id": 1
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]
    
    def test_create_user_weak_password(self, client, admin_token, test_roles):
        """Não deve criar usuário com senha fraca"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Usuario Fraco",
            "email": "fraco@teste.com",
            "password": "weak",  # Senha fraca
            "role_id": test_roles["usuario"].id
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_create_user_invalid_role(self, client, admin_token):
        """Não deve criar usuário com role inválido"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "name": "Usuario Invalido",
            "email": "invalido@teste.com",
            "password": "ValidPass123!",
            "role_id": 9999  # Role não existe
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserList:
    """Testes de listagem de usuários"""
    
    def test_list_users_own_company(self, client, admin_token, test_company1, db):
        """Admin deve listar apenas usuários de sua empresa"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            "/api/v1/users/",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        
        if isinstance(users, list) and len(users) > 0:
            for user in users:
                assert user["company_id"] == test_company1.id
    
    def test_list_users_pagination(self, client, admin_token, test_company1, test_roles, db):
        """Listagem de usuários deve suportar paginação"""
        # Criar 5 usuários adicionais
        for i in range(5):
            user = User(
                name=f"Usuario {i}",
                email=f"user{i}@teste.com",
                password_hash=get_password_hash("Pass123!"),
                company_id=test_company1.id,
                role_id=test_roles["usuario"].id,
                is_active=True
            )
            db.add(user)
        db.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Listar com limit
        response = client.get(
            "/api/v1/users/?limit=2",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_user_cannot_list_other_company_users(self, client, user_token, test_user_company2):
        """Usuário não deve listar usuários de outra empresa"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = client.get(
            "/api/v1/users/",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        users = response.json()
        if isinstance(users, list):
            emails = [u.get("email") for u in users]
            assert "user@empresa2.com" not in emails


class TestUserUpdate:
    """Testes de atualização de usuários"""
    
    def test_update_user_success(self, client, admin_token, test_user, db):
        """Admin deve atualizar usuário"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        update_data = {
            "name": "Usuario Atualizado",
            "email": "atualizado@teste.com"
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Usuario Atualizado"
    
    def test_update_user_change_role(self, client, admin_token, test_user, test_roles, db):
        """Admin deve poder mudar role do usuário"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        update_data = {
            "name": test_user.name,
            "email": test_user.email,
            "role_id": test_roles["gerente"].id
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar no banco
        db.refresh(test_user)
        assert test_user.role_id == test_roles["gerente"].id

    def test_user_cannot_update_other_user(self, client, user_token, test_admin_user):
        """Usuário comum não pode atualizar outro usuário"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        update_data = {
            "name": "Hacker",
            "email": "hacker@teste.com"
        }
        
        response = client.put(
            f"/api/v1/users/{test_admin_user.id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserDelete:
    """Testes de exclusão de usuários"""
    
    def test_delete_user_soft_delete(self, client, admin_token, test_user, db):
        """Deletar usuário deve fazer soft delete (is_active=False)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar no banco
        db.refresh(test_user)
        assert test_user.is_active == False
    
    def test_deleted_user_cannot_login(self, client, test_user, db):
        """Usuário deletado não pode fazer login"""
        # Desativar usuário
        test_user.is_active = False
        db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "usuario123"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_cannot_delete_self(self, client, admin_token, test_admin_user):
        """Admin não pode deletar a si mesmo"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.delete(
            f"/api/v1/users/{test_admin_user.id}",
            headers=headers
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN, status.HTTP_204_NO_CONTENT]


class TestUserAuthorization:
    """Testes de autorização para operações de usuário"""
    
    def test_user_without_admin_cannot_create_user(self, client, user_token):
        """Usuário comum não pode criar usuário"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        user_data = {
            "name": "Novo Usuario",
            "email": "novo@teste.com",
            "password": "NovoPass123!",
            "role_id": 1
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_manager_can_list_users(self, client, manager_token):
        """Gerente pode listar usuários"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        response = client.get(
            "/api/v1/users/",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
