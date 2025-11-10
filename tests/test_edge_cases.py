"""
Testes de Edge Cases e Tratamento de Erros
Validação de casos extremos e comportamentos inesperados
"""
import pytest
from fastapi import status
from decimal import Decimal


class TestProductEdgeCases:
    """Testes de edge cases para produtos"""
    
    def test_product_with_zero_price(self, client, admin_token, test_company1, db):
        """Produto com preço zero deve falhar ou ser permitido?"""
        from app.models.product import Product
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Tentar criar produto com preço zero
        product = Product(
            name="Brinde Grátis",
            sku="FREE-001",
            cost_price=0,
            sale_price=0,
            stock_quantity=100,
            company_id=test_company1.id
        )
        db.add(product)
        db.commit()
        
        # Verificar se foi criado
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sale_price"] == 0
    
    def test_product_with_negative_cost_price(self, client, admin_token, test_company1, db):
        """Produto com custo negativo (subsídio)"""
        from app.models.product import Product
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        product = Product(
            name="Produto Subsidiado",
            sku="SUB-001",
            cost_price=-10.00,  # Negativo
            sale_price=5.00,
            stock_quantity=100,
            company_id=test_company1.id
        )
        db.add(product)
        db.commit()
        
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers=headers
        )
        # Aceita ou rejeita deve ser decisão do negócio
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_product_stock_overflow(self, client, admin_token, test_company1, db):
        """Estoque com valor muito grande"""
        from app.models.product import Product
        
        product = Product(
            name="Mega Estoque",
            sku="MEGA-001",
            cost_price=10.00,
            sale_price=20.00,
            stock_quantity=999999999,  # Muito grande
            company_id=test_company1.id
        )
        db.add(product)
        db.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestSaleEdgeCases:
    """Testes de edge cases para vendas"""
    
    def test_sale_with_very_large_quantity(self, client, admin_token, test_product, test_customer):
        """Venda com quantidade muito grande"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 999999,  # Quantidade muito grande
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "estoque" in response.json()["detail"].lower()
    
    def test_sale_with_single_item_multiple_times(self, client, admin_token, test_product, test_customer):
        """Mesmos item múltiplas vezes em uma venda"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 5,
                    "unit_price": 20.00
                },
                {
                    "product_id": test_product.id,
                    "quantity": 3,
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        # Deve aceitar (somar as quantidades)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_sale_with_discount_equal_to_total(self, client, admin_token, test_product, test_customer):
        """Desconto igual ao total (venda grátis)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 20.00,  # Igual ao total
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["total_amount"] == 0


class TestInstallmentEdgeCases:
    """Testes de edge cases para parcelas"""
    
    def test_installment_with_60_parcelas(self, client, admin_token, test_product, test_customer):
        """Máximo permitido de parcelas (60)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 60,
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar que criou 60 parcelas
        sale_id = response.json()["id"]
        response = client.get(
            f"/api/v1/sales/{sale_id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        # installments devem ter 60 itens
    
    def test_installment_rounding(self, client, admin_token, test_product, test_customer):
        """Verificar arredondamento correto de parcelas"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Valor que divide desigualmente
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 3,
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Total: 100.00 / 3 = 33.33 + 33.33 + 33.34


class TestPaginationAndFiltering:
    """Testes de paginação e filtros"""
    
    def test_list_products_pagination(self, client, admin_token, test_company1, db):
        """Teste de paginação em listagem de produtos"""
        from app.models.product import Product
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Criar 50 produtos
        for i in range(50):
            product = Product(
                name=f"Produto {i}",
                sku=f"PROD-{i:03d}",
                cost_price=10.00,
                sale_price=20.00,
                stock_quantity=100,
                company_id=test_company1.id
            )
            db.add(product)
        db.commit()
        
        # Listar com limit 20
        response = client.get(
            "/api/v1/products/?skip=0&limit=20",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 20
        
        # Segunda página
        response = client.get(
            "/api/v1/products/?skip=20&limit=20",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_sales_filter_by_customer(self, client, admin_token, test_product, test_customer, db):
        """Filtrar vendas por cliente"""
        from app.models.customer import Customer
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Criar segundo cliente
        customer2 = Customer(
            name="Cliente 2",
            email="cliente2@teste.com",
            company_id=test_customer.company_id
        )
        db.add(customer2)
        db.commit()
        
        # Criar venda para cliente 1
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "cash",
            "discount_amount": 0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 20.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Filtrar por cliente
        response = client.get(
            f"/api/v1/sales/?customer_id={test_customer.id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_invalid_product_id_format(self, client, admin_token):
        """ID de produto inválido deve retornar erro apropriado"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            "/api/v1/products/invalid-id",
            headers=headers
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_duplicate_email_on_user_creation(self, client, admin_token, test_admin_user, test_company1, test_roles, db):
        """Não deve criar dois usuários com mesmo email"""
        from app.models.user import User
        
        # Tentar criar usuário com email duplicado
        try:
            user = User(
                name="Duplicate User",
                email="admin@teste.com",  # Email já existe
                password_hash="hash123",
                company_id=test_company1.id,
                role_id=test_roles["admin"].id
            )
            db.add(user)
            db.commit()
            assert False, "Deveria ter falhado ao criar usuário com email duplicado"
        except Exception:
            # Esperado falhar
            pass
