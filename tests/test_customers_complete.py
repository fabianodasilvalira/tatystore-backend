"""
Testes completos de Gestão de Clientes (Fase 4)
Criação, listagem, atualização, exclusão e validações de clientes
"""
import pytest
from fastapi import status
from app.models.customer import Customer


class TestCustomerCreation:
    """Testes de criação de clientes"""
    
    def test_create_customer_success(self, client, manager_token, test_company1):
        """Gerente deve criar novo cliente"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        customer_data = {
            "name": "Cliente Novo",
            "email": "cliente@novo.com",
            "phone": "11999999999",
            "cpf": "98765432100"
        }
        
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Cliente Novo"
    
    def test_create_customer_duplicate_cpf(self, client, manager_token, test_customer):
        """Não deve criar cliente com CPF duplicado"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        customer_data = {
            "name": "Outro Cliente",
            "email": "outro@cliente.com",
            "phone": "11988888888",
            "cpf": test_customer.cpf
        }
        
        response = client.post(
            "/api/v1/customers/",
            json=customer_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCustomerList:
    """Testes de listagem de clientes"""
    
    def test_list_customers_own_company_only(self, client, manager_token, test_company1, test_customer):
        """Gerente deve listar apenas clientes de sua empresa"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        response = client.get(
            "/api/v1/customers/",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        customers = response.json()
        if isinstance(customers, list):
            for customer in customers:
                assert customer.get("company_id") == test_company1.id
    
    def test_list_customers_pagination(self, client, manager_token, test_company1, test_roles, db):
        """Listagem de clientes deve suportar paginação"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        for i in range(10):
            customer = Customer(
                name=f"Cliente {i}",
                email=f"cliente{i}@teste.com",
                cpf=f"{i:011d}",
                company_id=test_company1.id
            )
            db.add(customer)
        db.commit()
        
        response = client.get(
            "/api/v1/customers/?limit=5",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if isinstance(data, list):
            assert len(data) <= 5


class TestCustomerUpdate:
    """Testes de atualização de clientes"""
    
    def test_update_customer_success(self, client, manager_token, test_customer):
        """Gerente deve atualizar cliente"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        update_data = {
            "name": "Cliente Atualizado",
            "email": "atualizado@cliente.com",
            "phone": "11999999999"
        }
        
        response = client.put(
            f"/api/v1/customers/{test_customer.id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Cliente Atualizado"


class TestCustomerDelete:
    """Testes de exclusão de clientes"""
    
    def test_delete_customer_soft_delete(self, client, manager_token, test_customer, db):
        """Deletar cliente deve fazer soft delete"""
        headers = {"Authorization": f"Bearer {manager_token}"}
        
        response = client.delete(
            f"/api/v1/customers/{test_customer.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        db.refresh(test_customer)
        assert test_customer.is_active == False
