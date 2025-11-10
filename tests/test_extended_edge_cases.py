"""
Testes Extendidos de Casos Extremos
Validar comportamentos limite, valores nulos, vazios e extremos
"""
import pytest
from fastapi import status
from decimal import Decimal
from datetime import date, timedelta
import uuid


class TestBoundaryValues:
    """Testes de valores limites"""
    
    def test_minimum_sale_amount(self, client, manager_token, test_customer, test_product):
        """Validar venda com valor mínimo (0.01)"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 0.01}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_maximum_installments_60(self, client, manager_token, test_customer, test_product):
        """Validar venda com máximo de 60 parcelas"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 6000.0}],
                "payment_type": "credit",
                "installments_count": 60,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_exceeds_maximum_installments(self, client, manager_token, test_customer, test_product):
        """Validar que não permite mais de 60 parcelas"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "credit",
                "installments_count": 61,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_maximum_quantity_per_item(self, client, manager_token, test_customer, test_product, db):
        """Validar venda com quantidade máxima"""
        from app.models.product import Product
        
        # Adicionar muito estoque
        test_product.stock_quantity = 10000
        db.commit()
        
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 9999, "unit_price": 1.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_maximum_discount_percentage(self, client, manager_token, test_customer, test_product):
        """Validar desconto máximo (100% do subtotal)"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 100.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["total_amount"] == 0.0
    
    def test_discount_exceeds_subtotal(self, client, manager_token, test_customer, test_product):
        """Validar que desconto não pode exceder subtotal"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 150.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestNullAndEmptyValues:
    """Testes de valores nulos e vazios"""
    
    def test_sale_with_empty_items_list(self, client, manager_token, test_customer):
        """Validar que venda com lista vazia de items é rejeitada"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_sale_with_zero_quantity_item(self, client, manager_token, test_customer, test_product):
        """Validar que item com quantidade zero é rejeitado"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 0, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_customer_with_null_email(self, client, manager_token):
        """Validar criação de cliente sem email"""
        response = client.post(
            "/api/v1/customers",
            json={
                "name": "Customer without email",
                "cpf": "444.444.444-04",
                "phone": "1199999999"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        # Pode ser aceito se email é opcional
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_product_with_empty_name(self, client, manager_token):
        """Validar que produto com nome vazio é rejeitado"""
        response = client.post(
            "/api/v1/products",
            json={
                "name": "",
                "description": "Test product",
                "price": 100.0,
                "stock_quantity": 10,
                "min_stock_level": 5
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSpecialCharactersAndEncoding:
    """Testes de caracteres especiais e codificação"""
    
    def test_customer_name_with_special_characters(self, client, manager_token, test_company1):
        """Validar criação de cliente com caracteres especiais"""
        response = client.post(
            "/api/v1/customers",
            json={
                "name": "João da Silva-Pereira & Filhos",
                "email": f"customer-{uuid.uuid4()}@example.com",
                "cpf": "12345678901",
                "phone": "1199999999"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_product_name_with_unicode(self, client, manager_token, test_company1):
        """Validar criação de produto com caracteres Unicode e acentuação"""
        unique_sku = f"SKU-UNICODE-{str(uuid.uuid4())[:8]}"
        response = client.post(
            "/api/v1/products",
            json={
                "name": "Produto com Acento: Açúcar Brasileiro™",
                "description": "Produto teste com Unicode: 中文 العربية",
                "sku": unique_sku,
                "barcode": str(uuid.uuid4()),
                "cost_price": 5.0,
                "sale_price": 10.0,
                "stock_quantity": 100,
                "min_stock": 5
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "Acento" in data["name"]
    
    def test_sale_notes_with_long_text(self, client, manager_token, test_customer, test_product):
        """Validar venda com notas de texto longo"""
        long_notes = "X" * 1000
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0,
                "notes": long_notes
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED


class TestTimeAndDateBoundaries:
    """Testes de limites de data e hora"""
    
    def test_installment_due_date_calculation(self, client, manager_token, test_customer, test_product, db):
        """Validar cálculo correto de datas de vencimento"""
        from app.models.sale import Sale
        from datetime import date, timedelta
        
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
        
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        
        # Validar que cada parcela vence 30 dias depois da anterior
        for i, installment in enumerate(sale.installments):
            expected_due_date = date.today() + timedelta(days=30 * (i + 1))
            assert installment.due_date == expected_due_date
    
    def test_payment_of_overdue_installment(self, client, manager_token, test_customer, test_product, db):
        """Validar pagamento de parcela vencida"""
        from app.models.sale import Sale
        from app.models.installment import Installment, InstallmentStatus
        from datetime import date, timedelta
        
        # Criar venda
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "credit",
                "installments_count": 1,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Forçar vencimento da parcela
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        first_installment = sale.installments[0]
        first_installment.due_date = date.today() - timedelta(days=10)  # 10 dias atrasado
        first_installment.status = InstallmentStatus.OVERDUE
        db.commit()
        
        # Pagar parcela vencida
        response = client.patch(
            f"/api/v1/installments/{first_installment.id}/pay",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que foi paga
        db.refresh(first_installment)
        assert first_installment.status == InstallmentStatus.PAID
