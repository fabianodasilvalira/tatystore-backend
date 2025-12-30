"""
Testes completos de Autenticação e Token Management (Fase 2)
Refresh token, logout, change password, token validation
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt


class TestRefreshToken:
    """Testes de refresh token"""
    
    def test_refresh_token_success(self, client, test_admin_user, db):
        """Refresh token deve gerar novo access token"""
        # Primeiro fazer login para obter refresh token
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@teste.com", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_200_OK
        refresh_token = response.json().get("refresh_token")
        
        # Verificar que refresh_token foi retornado
        assert refresh_token is not None, "Refresh token should be returned on login"
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar que novo access_token foi gerado
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_expired(self, client):
        """Refresh token expirado deve falhar"""
        # Criar refresh token expirado
        expired_payload = {
            "sub": "1",
            "user_id": 1,
            "company_id": 1,
            "role_id": 1,
            "type": "refresh",
            "exp": datetime.utcnow() - timedelta(days=1)
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_refresh_token_format(self, client):
        """Token com formato inválido deve falhar"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.format"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_token_used_as_refresh_token(self, client, admin_token):
        """Access token não deve funcionar como refresh token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutToken:
    """Testes de logout e invalidação de token"""
    
    def test_logout_with_valid_token(self, client, admin_token):
        """Logout deve invalidar token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/api/v1/auth/logout",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
    
    def test_logout_without_token(self, client):
        """Logout sem token deve falhar"""
        response = client.post(
            "/api/v1/auth/logout"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenValidation:
    """Testes de validação de token"""
    
    def test_token_expired_returns_401(self, client):
        """Token expirado deve retornar 401"""
        # Criar access token expirado
        expired_payload = {
            "sub": "1",
            "user_id": 1,
            "company_id": 1,
            "role_id": 1,
            "type": "access",
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_token_returns_401(self, client):
        """Token inválido deve retornar 401"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_without_bearer_prefix_fails(self, client, admin_token):
        """Token sem 'Bearer' prefix deve falhar"""
        headers = {"Authorization": admin_token}
        response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """Testes de mudança de senha"""
    
    def test_change_password_success(self, client, test_admin_user, admin_token):
        """Usuário pode mudar sua senha"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        password_data = {
            "old_password": "admin123",
            "new_password": "NewPass123!"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()
    
    def test_change_password_wrong_old_password(self, client, admin_token):
        """Mudar senha com senha antiga incorreta deve falhar"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "NewPass123!"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_weak_new_password(self, client, admin_token):
        """Nova senha fraca deve ser rejeitada"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        password_data = {
            "old_password": "admin123",
            "new_password": "weak"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
