"""
Testes para Endpoints de Perfil de Usuário
Testa GET /users/me, PUT /users/me e POST /auth/change-password
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.role import Role
from app.models.company import Company
from app.core.security import hash_password, verify_password


client = TestClient(app)


def test_get_my_profile_success(db: Session):
    """Teste: Obter perfil próprio com sucesso"""
    # Criar empresa
    company = Company(
        name="Test Company",
        slug="test-company",
        cnpj="12345678000190",
        email="test@company.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Criar role
    role = db.query(Role).filter(Role.name == "Gerente").first()
    if not role:
        role = Role(name="Gerente", description="Gerente")
        db.add(role)
        db.flush()
    
    # Criar usuário
    user = User(
        name="Test User",
        email="testuser@test.com",
        password_hash=hash_password("test123"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "testuser@test.com",
        "password": "test123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Obter perfil
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@test.com"
    assert data["name"] == "Test User"
    assert data["company_id"] == company.id


def test_update_my_profile_name_success(db: Session):
    """Teste: Atualizar nome do perfil com sucesso"""
    # Criar empresa
    company = Company(
        name="Test Company 2",
        slug="test-company-2",
        cnpj="12345678000191",
        email="test2@company.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Criar role
    role = db.query(Role).filter(Role.name == "Gerente").first()
    if not role:
        role = Role(name="Gerente", description="Gerente")
        db.add(role)
        db.flush()
    
    # Criar usuário
    user = User(
        name="Old Name",
        email="update@test.com",
        password_hash=hash_password("test123"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "update@test.com",
        "password": "test123"
    })
    token = login_response.json()["access_token"]
    
    # Atualizar nome
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["email"] == "update@test.com"  # Email não mudou


def test_update_my_profile_email_duplicate_rejected(db: Session):
    """Teste: Rejeitar atualização de email duplicado"""
    # Criar empresa
    company = Company(
        name="Test Company 3",
        slug="test-company-3",
        cnpj="12345678000192",
        email="test3@company.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Criar role
    role = db.query(Role).filter(Role.name == "Gerente").first()
    if not role:
        role = Role(name="Gerente", description="Gerente")
        db.add(role)
        db.flush()
    
    # Criar dois usuários
    user1 = User(
        name="User 1",
        email="user1@test.com",
        password_hash=hash_password("test123"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    user2 = User(
        name="User 2",
        email="user2@test.com",
        password_hash=hash_password("test123"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    db.add_all([user1, user2])
    db.commit()
    
    # Login como user2
    login_response = client.post("/api/v1/auth/login", json={
        "email": "user2@test.com",
        "password": "test123"
    })
    token = login_response.json()["access_token"]
    
    # Tentar atualizar email para o email do user1
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "user1@test.com"}
    )
    
    assert response.status_code == 400
    assert "já cadastrado" in response.json()["detail"].lower()


def test_change_password_success(db: Session):
    """Teste: Alterar senha com sucesso"""
    # Criar empresa
    company = Company(
        name="Test Company 4",
        slug="test-company-4",
        cnpj="12345678000193",
        email="test4@company.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Criar role
    role = db.query(Role).filter(Role.name == "Gerente").first()
    if not role:
        role = Role(name="Gerente", description="Gerente")
        db.add(role)
        db.flush()
    
    # Criar usuário
    user = User(
        name="Password Test",
        email="password@test.com",
        password_hash=hash_password("oldpass123"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Login com senha antiga
    login_response = client.post("/api/v1/auth/login", json={
        "email": "password@test.com",
        "password": "oldpass123"
    })
    token = login_response.json()["access_token"]
    
    # Alterar senha
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "oldpass123",
            "new_password": "newpass123"
        }
    )
    
    assert response.status_code == 200
    assert "sucesso" in response.json()["message"].lower()
    
    # Verificar que a nova senha funciona
    login_new = client.post("/api/v1/auth/login", json={
        "email": "password@test.com",
        "password": "newpass123"
    })
    assert login_new.status_code == 200


def test_change_password_wrong_old_password(db: Session):
    """Teste: Rejeitar alteração de senha com senha antiga incorreta"""
    # Criar empresa
    company = Company(
        name="Test Company 5",
        slug="test-company-5",
        cnpj="12345678000194",
        email="test5@company.com",
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Criar role
    role = db.query(Role).filter(Role.name == "Gerente").first()
    if not role:
        role = Role(name="Gerente", description="Gerente")
        db.add(role)
        db.flush()
    
    # Criar usuário
    user = User(
        name="Wrong Pass Test",
        email="wrongpass@test.com",
        password_hash=hash_password("correctpass"),
        company_id=company.id,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "correctpass"
    })
    token = login_response.json()["access_token"]
    
    # Tentar alterar senha com senha antiga errada
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "wrongoldpass",
            "new_password": "newpass123"
        }
    )
    
    assert response.status_code == 400
    assert "incorreta" in response.json()["detail"].lower()


def test_super_admin_can_edit_own_profile(db: Session):
    """Teste: Super Admin pode editar seu próprio perfil"""
    # Criar role Super Admin
    super_admin_role = db.query(Role).filter(Role.name == "Super Admin").first()
    if not super_admin_role:
        super_admin_role = Role(name="Super Admin", description="Super Admin")
        db.add(super_admin_role)
        db.flush()
    
    # Criar Super Admin (sem company_id)
    super_admin = User(
        name="Super Admin",
        email="superadmin@test.com",
        password_hash=hash_password("admin123"),
        company_id=None,  # Super Admin não tem empresa
        role_id=super_admin_role.id,
        is_active=True
    )
    db.add(super_admin)
    db.commit()
    
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "superadmin@test.com",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Atualizar perfil
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Super Admin Updated"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Super Admin Updated"
