"""
Testes abrangentes para o sistema de pagamento de parcelas
Cobre todos os cenários: valores parciais, valores negativos, valores acima do restante, etc.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, date

from app.models.installment import Installment, InstallmentStatus
from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
from app.models.sale import Sale, SaleItem, PaymentType, SaleStatus


class TestPartialPayments:
    """Testes para pagamentos parciais com valores diversos"""
    
    def test_payment_exact_half_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa pagamento de exatamente metade do valor da parcela"""
        # Criar venda a prazo
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 200.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        sale_id = response.json()["id"]
        
        # Buscar a parcela criada
        installment = db.query(Installment).filter(Installment.sale_id == sale_id).first()
        assert installment is not None
        assert float(installment.amount) == 200.00
        
        # Pagar metade
        payment_data = {"amount": 100.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        assert payment["amount_paid"] == 100.00
        
        # Verificar saldo restante
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_paid"] == 100.00
        assert data["remaining_amount"] == 100.00
        assert data["status"] == InstallmentStatus.PENDING
    
    def test_payment_multiple_small_amounts(self, client, admin_token, test_product, test_customer, db):
        """Testa múltiplos pagamentos de pequenos valores"""
        # Criar venda de R$ 300
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 3,
                    "unit_price": 100.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Fazer 6 pagamentos de R$ 50
        payments_made = []
        for i in range(6):
            payment_data = {"amount": 50.00}
            response = client.post(
                f"/api/v1/installment-payments/{installment.id}/pay",
                json=payment_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == status.HTTP_201_CREATED
            payments_made.append(response.json())
        
        # Verificar que todos os pagamentos foram registrados
        assert len(payments_made) == 6
        
        # Verificar saldo final
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["total_paid"] == 300.00
        assert data["remaining_amount"] == 0.00
        assert data["status"] == InstallmentStatus.PAID
    
    def test_payment_odd_amounts(self, client, admin_token, test_product, test_customer, db):
        """Testa pagamentos com valores quebrados (decimais)"""
        # Criar venda de R$ 157.89
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 157.89
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar R$ 57.34
        payment_data = {"amount": 57.34}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Pagar R$ 100.55 (completa o pagamento)
        payment_data = {"amount": 100.55}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar pagamento completo
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["total_paid"] == 157.89
        assert data["remaining_amount"] == 0.00
        assert data["status"] == InstallmentStatus.PAID


class TestPaymentValidations:
    """Testes para validações de pagamento"""
    
    def test_payment_negative_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa que valores negativos são rejeitados"""
        # Criar venda
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
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
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Tentar pagar com valor negativo
        payment_data = {"amount": -50.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail = response.json().get("detail", "")
        if isinstance(detail, list):
            # Pydantic retorna lista de erros de validação
            detail_str = str(detail[0].get("msg", "")) if detail else ""
        else:
            detail_str = detail.lower() if isinstance(detail, str) else str(detail)
        
        assert "maior que zero" in detail_str.lower() or "obrigatório" in detail_str.lower() or "value_error" in detail_str.lower() or "greater than 0" in detail_str.lower()
    
    def test_payment_zero_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa que valor zero é rejeitado"""
        # Criar venda
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
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
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Tentar pagar com valor zero
        payment_data = {"amount": 0.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_payment_exceeds_remaining_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa que pagamento acima do valor restante é rejeitado"""
        # Criar venda de R$ 100
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
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
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar R$ 60
        payment_data = {"amount": 60.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Tentar pagar R$ 50 (excede o restante de R$ 40)
        payment_data = {"amount": 50.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "excede" in response.json()["detail"].lower()
    
    def test_payment_after_full_payment(self, client, admin_token, test_product, test_customer, db):
        """Testa que não é possível pagar parcela já quitada"""
        # Criar venda de R$ 100
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
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
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar valor total
        payment_data = {"amount": 100.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Tentar pagar novamente
        payment_data = {"amount": 10.00}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Deve rejeitar pois não há saldo restante
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_payment_installment_not_found(self, client, admin_token):
        """Testa pagamento de parcela inexistente"""
        payment_data = {"amount": 50.00}
        response = client.post(
            "/api/v1/installment-payments/99999/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrada" in response.json()["detail"].lower()


class TestRemainingAmountCalculation:
    """Testes específicos para cálculo correto do valor devido"""
    
    def test_remaining_amount_after_single_payment(self, client, admin_token, test_product, test_customer, db):
        """Testa cálculo do valor restante após um pagamento"""
        # Criar parcela de R$ 500
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 500.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar R$ 123.45
        payment_data = {"amount": 123.45}
        client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verificar cálculo correto
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["amount"] == 500.00
        assert data["total_paid"] == 123.45
        assert data["remaining_amount"] == 376.55
    
    def test_remaining_amount_after_multiple_payments(self, client, admin_token, test_product, test_customer, db):
        """Testa cálculo acumulado após múltiplos pagamentos"""
        # Criar parcela de R$ 1000
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 1000.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Fazer vários pagamentos
        payments = [250.00, 100.50, 75.25, 200.00]
        for amount in payments:
            payment_data = {"amount": amount}
            client.post(
                f"/api/v1/installment-payments/{installment.id}/pay",
                json=payment_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # Verificar saldo
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        expected_paid = sum(payments)  # 625.75
        expected_remaining = 1000.00 - expected_paid  # 374.25
        
        assert data["total_paid"] == expected_paid
        assert data["remaining_amount"] == expected_remaining
        assert data["status"] == InstallmentStatus.PENDING


class TestPaymentHistory:
    """Testes para histórico de pagamentos"""
    
    def test_payment_history_list(self, client, admin_token, test_product, test_customer, db):
        """Testa listagem do histórico de pagamentos"""
        # Criar venda
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 300.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Fazer 3 pagamentos
        amounts = [100.00, 50.00, 150.00]
        for amount in amounts:
            payment_data = {"amount": amount}
            client.post(
                f"/api/v1/installment-payments/{installment.id}/pay",
                json=payment_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # Listar histórico
        response = client.get(
            f"/api/v1/installment-payments/installments/{installment.id}/payments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        
        # Verificar valores
        payment_amounts = [p["amount_paid"] for p in data["items"]]
        assert sorted(payment_amounts) == sorted(amounts)


class TestEdgeCases:
    """Testes para casos extremos"""
    
    def test_payment_very_small_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa pagamento de valor muito pequeno (centavos)"""
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 10.00
                }
            ]
        }
        
        response = client.post(
            "/api/v1/sales/",
            json=sale_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar R$ 0.01
        payment_data = {"amount": 0.01}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar saldo
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["total_paid"] == 0.01
        assert data["remaining_amount"] == 9.99
    
    def test_payment_exact_remaining_amount(self, client, admin_token, test_product, test_customer, db):
        """Testa pagamento do valor exato restante"""
        sale_data = {
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
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
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        installment = db.query(Installment).filter(
            Installment.sale_id == response.json()["id"]
        ).first()
        
        # Pagar R$ 37.50
        payment_data = {"amount": 37.50}
        client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Pagar exatamente o restante: R$ 62.50
        payment_data = {"amount": 62.50}
        response = client.post(
            f"/api/v1/installment-payments/{installment.id}/pay",
            json=payment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar que está quitado
        response = client.get(
            f"/api/v1/installments/{installment.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["total_paid"] == 100.00
        assert data["remaining_amount"] == 0.00
        assert data["status"] == InstallmentStatus.PAID
