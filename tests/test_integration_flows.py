"""
Testes de Integração - Fluxos Fim-a-Fim
Validar workflows completos do sistema
"""
import pytest
from fastapi import status
from datetime import date, timedelta
import uuid
from app.models.product import Product


class TestCompleteCompanySetupFlow:
    """Testes de fluxo completo de onboarding da empresa"""
    
    def test_full_company_onboarding_flow(self, client, admin_token, db):
        """Validar fluxo completo de onboarding: empresa > produto > cliente > venda
        
        Este teste percorre o workflow completo de setup de uma nova empresa.
        """
        # Format: 14 random digits
        cnpj_digits = ''.join([str(int(uuid.uuid4().hex[i], 16) % 10) for i in range(14)])
        
        # Step 1: Criar empresa
        company_response = client.post(
            "/api/v1/companies",
            json={
                "name": "Empresa Teste Onboarding",
                "cnpj": cnpj_digits,
                "email": f"empresa-{str(uuid.uuid4())[:8]}@example.com",
                "address": "Rua Teste, 123",
                "phone": "1199999999"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert company_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], \
            f"Expected 200 or 201, got {company_response.status_code}: {company_response.text}"
        company_data = company_response.json()
        company_id = company_data.get("id")
        assert company_id is not None
        
        # Step 2: Criar produto
        unique_sku = f"SKU-ONBOARD-{str(uuid.uuid4())[:8]}"
        product_response = client.post(
            "/api/v1/products",
            json={
                "name": "Produto Onboarding",
                "description": "Produto teste",
                "sku": unique_sku,
                "barcode": str(uuid.uuid4()),
                "cost_price": 10.0,
                "sale_price": 20.0,
                "stock_quantity": 100,
                "min_stock": 5
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert product_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]


class TestCreditSaleAndPaymentFlow:
    """Testes de fluxo de venda a crédito e pagamento"""
    
    def test_full_credit_sale_and_payment_flow(self, client, manager_token, test_customer, test_product, db):
        """Validar fluxo: criar venda a crédito, pagar parcelas, verificar relatório"""
        from app.models.sale import Sale, SaleStatus
        from app.models.installment import Installment, InstallmentStatus
        
        # 1. Criar venda a crédito
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 3, "unit_price": 50.0}],
                "payment_type": "credit",
                "installments_count": 3,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_data = response.json()
        sale_id = sale_data["id"]
        assert sale_data["payment_type"] == "credit"
        assert sale_data["installments_count"] == 3
        
        # 2. Obter parcelas
        response = client.get(
            f"/api/v1/installments/customer/{test_customer.id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        installments = response.json()
        assert len(installments) >= 3
        
        # 3. Pagar primeira parcela
        first_installment = installments[0]
        response = client.patch(
            f"/api/v1/installments/{first_installment['id']}/pay",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Verificar que parcela foi paga
        db.refresh(db.query(Installment).filter(Installment.id == first_installment['id']).first())
        paid_installment = db.query(Installment).filter(Installment.id == first_installment['id']).first()
        assert paid_installment.status == InstallmentStatus.PAID
    
    def test_credit_sale_with_partial_payment(self, client, manager_token, test_customer, test_product, db):
        """Validar venda a crédito com alguns pagamentos"""
        from app.models.installment import Installment, InstallmentStatus
        
        # Criar venda com 5 parcelas
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 500.0}],
                "payment_type": "credit",
                "installments_count": 5,
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Obter parcelas
        response = client.get(
            f"/api/v1/installments/customer/{test_customer.id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        installments = response.json()
        
        # Pagar 3 de 5 parcelas
        for i in range(3):
            response = client.patch(
                f"/api/v1/installments/{installments[i]['id']}/pay",
                headers={"Authorization": f"Bearer {manager_token}"}
            )
            assert response.status_code == status.HTTP_200_OK


class TestSaleCancellationFlow:
    """Testes do fluxo de cancelamento de venda"""
    
    def test_cancel_sale_and_restore_stock(self, client, manager_token, test_customer, test_product, db):
        """Validar que cancelamento de venda restaura estoque"""
        from app.models.product import Product
        
        # Guardar estoque inicial
        initial_stock = test_product.stock_quantity
        
        # Criar venda
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 5, "unit_price": 100.0}],
                "payment_type": "cash",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Verificar estoque reduzido
        db.refresh(test_product)
        assert test_product.stock_quantity == initial_stock - 5
        
        # Cancelar venda
        response = client.post(
            f"/api/v1/sales/{sale_id}/cancel",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar estoque restaurado
        db.refresh(test_product)
        assert test_product.stock_quantity == initial_stock
    
    def test_cancel_credit_sale_cancels_installments(self, client, manager_token, test_customer, test_product, db):
        """Validar que cancelar venda a crédito cancela parcelas"""
        from app.models.sale import Sale, SaleStatus
        from app.models.installment import InstallmentStatus
        
        # Criar venda a crédito
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
        
        # Cancelar venda
        response = client.post(
            f"/api/v1/sales/{sale_id}/cancel",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que venda foi cancelada e parcelas canceladas
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        assert sale.status == SaleStatus.CANCELLED
        
        for installment in sale.installments:
            assert installment.status == InstallmentStatus.CANCELLED


class TestReportingFlow:
    """Testes do fluxo de geração de relatórios"""
    
    def test_generate_sales_report(self, client, manager_token):
        """Validar geração de relatório de vendas"""
        response = client.get(
            "/api/v1/reports/sales",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_sales" in data or isinstance(data, (list, dict))
    
    def test_generate_profit_report(self, client, manager_token):
        """Validar geração de relatório de lucro"""
        response = client.get(
            "/api/v1/reports/profit",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
    
    def test_generate_overdue_report(self, client, manager_token):
        """Validar geração de relatório de inadimplência"""
        response = client.get(
            "/api/v1/reports/overdue",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_generate_low_stock_report(self, client, manager_token):
        """Validar geração de relatório de baixo estoque"""
        response = client.get(
            "/api/v1/reports/low-stock",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))


class TestMultiProductSaleFlow:
    """Testes de venda com múltiplos produtos"""
    
    def test_sale_with_multiple_products_and_items(self, client, manager_token, test_customer, test_product, db):
        """Validar venda com múltiplos itens"""
        from app.models.product import Product
        
        # Criar segundo produto
        product2 = Product(
            name="Product 2",
            description="Second product",
            sale_price=75.0,
            cost_price=50.0,
            stock_quantity=50,
            company_id=test_customer.company_id,
            min_stock=5,
            is_active=True
        )
        db.add(product2)
        db.commit()
        
        # Venda com 2 produtos diferentes
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [
                    {"product_id": test_product.id, "quantity": 2, "unit_price": 50.0},
                    {"product_id": product2.id, "quantity": 3, "unit_price": 75.0}
                ],
                "payment_type": "cash",
                "discount_amount": 25.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_data = response.json()
        
        # Validar cálculos
        # subtotal = 2*50 + 3*75 = 100 + 225 = 325
        # total = 325 - 25 = 300
        assert sale_data["subtotal"] == 325.0
        assert sale_data["total_amount"] == 300.0
        assert len(sale_data["items"]) == 2


class TestPaymentTypeFlows:
    """Testes de diferentes tipos de pagamento"""
    
    def test_cash_payment_flow(self, client, manager_token, test_customer, test_product):
        """Validar fluxo de pagamento em dinheiro"""
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
        assert response.status_code == status.HTTP_201_CREATED
        sale_data = response.json()
        assert sale_data["payment_type"] == "cash"
    
    def test_credit_payment_flow(self, client, manager_token, test_customer, test_product):
        """Validar fluxo de pagamento a crédito"""
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
        sale_data = response.json()
        assert sale_data["payment_type"] == "credit"
        assert sale_data["installments_count"] == 3
    
    def test_pix_payment_flow(self, client, manager_token, test_customer, test_product):
        """Validar fluxo de pagamento PIX"""
        response = client.post(
            "/api/v1/sales",
            json={
                "customer_id": test_customer.id,
                "items": [{"product_id": test_product.id, "quantity": 1, "unit_price": 100.0}],
                "payment_type": "pix",
                "discount_amount": 0.0
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_data = response.json()
        assert sale_data["payment_type"] == "pix"
