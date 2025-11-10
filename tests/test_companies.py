"""
Testes de Empresas
"""
import pytest
from tests.conftest import get_auth_headers


def test_create_company_success(client):
    """
    Teste: Criar empresa com dados válidos deve retornar URL de acesso
    """
    response = client.post(
        "/api/v1/companies/",
        json={
            "name": "Nova Empresa",
            "cnpj": "11222333000144",
            "email": "contato@novaempresa.com",
            "phone": "11999887766"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "slug" in data
    assert "access_url" in data
    assert "nova-empresa" in data["slug"]
    assert data["slug"] in data["access_url"]


def test_create_company_duplicate_cnpj(client, test_company1):
    """
    Teste: CNPJ duplicado deve falhar
    """
    response = client.post(
        "/api/v1/companies/",
        json={
            "name": "Outra Empresa",
            "cnpj": test_company1.cnpj,
            "email": "outro@email.com",
            "phone": "11888776655"
        }
    )
    
    assert response.status_code == 400
    assert "já cadastrado" in response.json()["detail"].lower()


def test_list_companies_admin_only(client, admin_token, user_token):
    """
    Usando get_auth_headers para passar token nos headers
    Teste: Apenas admin pode listar todas as empresas
    """
    # Admin pode listar
    response = client.get(
        "/api/v1/companies/",
        headers=get_auth_headers(admin_token)
    )
    assert response.status_code == 200
    
    # Usuário comum não pode
    response = client.get(
        "/api/v1/companies/",
        headers=get_auth_headers(user_token)
    )
    assert response.status_code == 403


def test_get_my_company(client, admin_token, test_company1):
    """
    Usando get_auth_headers
    Teste: Usuário pode ver dados da própria empresa
    """
    response = client.get(
        "/api/v1/companies/me",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_company1.id
    assert data["name"] == test_company1.name


def test_update_company_own(client, admin_token, test_company1):
    """
    Usando get_auth_headers
    Teste: Admin pode atualizar própria empresa
    """
    response = client.put(
        f"/api/v1/companies/{test_company1.id}",
        headers=get_auth_headers(admin_token),
        json={"name": "Nome Atualizado"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nome Atualizado"


def test_cannot_update_other_company(client, admin_token, test_company2):
    """
    Usando get_auth_headers
    Teste: Não pode atualizar empresa de outra empresa
    """
    response = client.put(
        f"/api/v1/companies/{test_company2.id}",
        headers=get_auth_headers(admin_token),
        json={"name": "Tentativa de Ataque"}
    )
    
    assert response.status_code in [403, 404]
