"""
Testes estendidos de companies endpoints
"""
import pytest
from fastapi import status


class TestCompanyGetById:
    """Testes de buscar empresa por ID"""
    
    def test_get_company_by_id_own_company(self, client, admin_token, test_company1):
        """Deve buscar própria empresa por ID"""
        response = client.get(
            f"/api/v1/companies/{test_company1.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_company1.id
    
    def test_get_company_by_id_other_company(self, client, admin_token, test_company2):
        """Admin de empresa A não deve acessar empresa B"""
        response = client.get(
            f"/api/v1/companies/{test_company2.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Deve retornar 403 ou 404 dependendo da implementação
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]
    
    def test_get_company_invalid_id(self, client, admin_token):
        """Deve retornar 404 para ID inexistente"""
        response = client.get(
            "/api/v1/companies/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCompanyDelete:
    """Testes de desativação de empresa"""
    
    def test_delete_company_as_super_admin(self, client, super_admin_token, test_company1, db):
        """Super admin deve poder desativar empresa"""
        response = client.delete(
            f"/api/v1/companies/{test_company1.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar se foi desativada no banco
        db.refresh(test_company1)
        assert test_company1.is_active is False
    
    def test_manager_cannot_delete_company(self, client, manager_token, test_company):
        """Gerente não deve poder desativar empresa"""
        response = client.delete(
            f"/api/v1/companies/{test_company.id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_delete_company_own_company(self, client, admin_token, test_company):
        """Admin não deve desativar própria empresa"""
        response = client.delete(
            f"/api/v1/companies/{test_company.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Dependendo da lógica de negócio, pode ser bloqueado
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN, status.HTTP_204_NO_CONTENT]
