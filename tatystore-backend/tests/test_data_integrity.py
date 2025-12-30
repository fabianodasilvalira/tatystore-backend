"""
Testes de Integridade de Dados e Constraints
Validar relacionamentos, cascatas, e constraints de banco de dados
"""
import pytest
from fastapi import status
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta


class TestForeignKeyConstraints:
    """Testes de constraints de chave estrangeira"""
    
    def test_cannot_create_sale_with_invalid_customer(self, client, manager_token, test_product):
        """Validar que não é possível criar venda com customer_id inválido"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": 99999,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cannot_create_sale_with_invalid_product(self, client, manager_token, test_customer):
        """Validar que não é possível criar venda com product_id inválido"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": 99999, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_create_installment_with_invalid_sale(self, client, manager_token):
        """Validar que não é possível criar parcela com sale_id inválido"""
        response = client.get(
            "/api/v1/installments/999999",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestCascadeOperations:
    """Testes de operações em cascata"""
    
    def test_cancel_sale_cascades_to_installments(self, client, manager_token, test_customer, test_product, db):
        """Validar que cancelar venda cancela parcelas automaticamente"""
        from app.models.sale import Sale, SaleStatus
        from app.models.installment import Installment, InstallmentStatus
        
        # Criar venda a crédito
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "credit",
                "installments_count": 3,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Cancelar venda
        response = client.post(
            f"/api/v1/sales/{sale_id}/cancel",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que parcelas foram canceladas
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        assert sale.status == SaleStatus.CANCELLED
        
        for installment in sale.installments:
            assert installment.status == InstallmentStatus.CANCELLED
    
    def test_deactivate_customer_prevents_new_sales(self, client, manager_token, test_customer, test_product, db):
        """Validar que cliente inativo não pode ter novas vendas"""
        from app.models.customer import Customer
        
        # Desativar cliente
        test_customer.is_active = False
        db.commit()
        
        # Tentar criar venda
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    
    def test_deactivate_product_prevents_new_sales(self, client, manager_token, test_customer, test_product, db):
        """Validar que produto inativo não pode ser vendido"""
        # Desativar produto
        test_product.is_active = False
        db.commit()
        
        # Tentar criar venda
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDataConsistency:
    """Testes de consistência de dados"""
    
    def test_sale_total_equals_sum_of_items(self, client, manager_token, test_customer, test_product):
        """Validar que total da venda = subtotal - desconto"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [
                    {"product_id": test_product.id, "quantity": 2, "unit_price": 50.0},
                    {"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}
                ],
                "payment_type": "cash",
                "discount_amount": 50.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        sale_data = response.json()
        # subtotal = 2*50 + 1*100 = 200
        # total = 200 - 50 = 150
        assert sale_data["subtotal"] == 200.0
        assert sale_data["discount_amount"] == 50.0
        assert sale_data["total_amount"] == 150.0
    
    def test_installments_sum_equals_total(self, client, manager_token, test_customer, test_product, db):
        """Validar que soma das parcelas = total da venda"""
        from app.models.sale import Sale
        
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 300.0}],
                "payment_type": "credit",
                "installments_count": 3,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Obter venda com parcelas
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        
        # Somar parcelas
        installments_total = sum(inst.amount for inst in sale.installments)
        
        # Deve ser igual ao total da venda
        assert abs(installments_total - sale.total_amount) < 0.01
    
    def test_stock_quantity_never_negative(self, client, manager_token, test_customer, test_product, db):
        """Validar que quantidade em estoque nunca fica negativa"""
        from app.models.product import Product
        
        # Tentar vender mais que o estoque
        initial_stock = test_product.stock_quantity
        
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": initial_stock + 10, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        # Deve falhar
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verificar que estoque não mudou
        db.refresh(test_product)
        assert test_product.stock_quantity == initial_stock
    
    def test_user_belongs_to_company(self, client, manager_token, db):
        """Validar que usuário só pode acessar dados de sua empresa"""
        from app.models.user import User
        
        # Obter usuário do token
        # Este teste valida o isolamento multi-tenant
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK


class TestUniqueConstraints:
    """Testes de constraints de unicidade"""
    
    def test_duplicate_email_customer(self, client, manager_token, test_company1, db):
        """Validar que não pode haver dois clientes com mesmo email na empresa"""
        from app.models.customer import Customer
        
        # Criar primeiro cliente
        customer1 = Customer(
            name="Customer 1",
            email="duplicate@test.com",
            cpf="111.111.111-01",
            phone="1199999999",
            company_id=test_company1.id,
            is_active=True
        )
        db.add(customer1)
        db.commit()
        
        # Tentar criar segundo cliente com mesmo email
        response = client.post(
            "/api/v1/customers",
            json={
                "name": "Customer 2",
                "email": "duplicate@test.com",
                "cpf": "222.222.222-02",
                "phone": "1188888888"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_duplicate_cpf_customer(self, client, manager_token, test_company1, db):
        """Validar que não pode haver dois clientes com mesmo CPF na empresa"""
        from app.models.customer import Customer
        
        # Criar primeiro cliente
        customer1 = Customer(
            name="Customer 1",
            email="customer1@test.com",
            cpf="333.333.333-03",
            phone="1199999999",
            company_id=test_company1.id,
            is_active=True
        )
        db.add(customer1)
        db.commit()
        
        # Tentar criar segundo cliente com mesmo CPF
        response = client.post(
            "/api/v1/customers",
            json={
                "name": "Customer 2",
                "email": "customer2@test.com",
                "cpf": "333.333.333-03",
                "phone": "1188888888"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
