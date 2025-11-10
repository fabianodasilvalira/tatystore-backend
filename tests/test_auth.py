"""
Testes de Autenticação e Autorização
"""
import pytest
from tests.conftest import get_auth_headers


def test_login_with_json_success(client, test_admin_user):
    """
    Teste: Login com JSON deve retornar token
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "admin123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@teste.com"
    assert "company_id" in data["user"]
    assert "company_slug" in data["user"]


def test_login_wrong_password(client, test_admin_user):
    """
    Teste: Login com senha errada deve falhar
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "senhaerrada"}
    )
    
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """
    Teste: Login com usuário inexistente deve falhar
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inexistente@teste.com", "password": "senha"}
    )
    
    assert response.status_code == 401


def test_token_includes_company_and_role(client, test_admin_user):
    """
    Teste: Token deve incluir company_slug e role
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "admin123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    user = data["user"]
    assert user["company_slug"] == "empresa-teste-1"
    assert user["role"] == "admin"


def test_get_current_user(client, admin_token):
    """
    Teste: Endpoint /me deve retornar dados do usuário
    Usando get_auth_headers para passar token corretamente
    """
    headers = get_auth_headers(admin_token)
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@teste.com"
    assert data["role"] == "admin"
    assert data["company_slug"] == "empresa-teste-1"


def test_access_protected_route_without_token(client):
    """
    Teste: Acesso sem token deve retornar 401 ou 403
    """
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code in [401, 403]


def test_access_with_invalid_token(client):
    """
    Teste: Token inválido deve retornar 401
    """
    headers = {"Authorization": "Bearer token_invalido"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


def test_inactive_user_cannot_login(client, test_admin_user, db):
    """
    Teste: Usuário desativado não pode fazer login
    """
    test_admin_user.is_active = False
    db.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "admin123"}
    )
    
    assert response.status_code == 403


def test_inactive_company_blocks_login(client, test_admin_user, test_company1, db):
    """
    Teste: Empresa desativada bloqueia login
    """
    test_company1.is_active = False
    db.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "admin123"}
    )
    
    assert response.status_code == 403
