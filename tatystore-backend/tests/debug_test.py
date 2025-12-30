import pytest
from fastapi import status

def test_debug_duplicate(client, test_company1, db):
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

    # Login
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
    
    with open("/tmp/debug_result.txt", "w") as f:
        f.write(f"Status: {response.status_code}\n")
        f.write(f"Body: {response.text}\n")
    
    # Assert deve falhar ou passar, mas o arquivo sera escrito
    assert response.status_code == status.HTTP_400_BAD_REQUEST
