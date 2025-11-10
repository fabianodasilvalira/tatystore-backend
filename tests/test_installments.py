"""
Testes de Parcelas
"""
import pytest
from datetime import datetime, timedelta
from tests.conftest import get_auth_headers


def test_pay_installment_success(client, admin_token, test_product, test_customer, db):
    """
    Teste: Pagar parcela com sucesso
    """
    # Criar venda a crédito via API
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 2,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        }
    )
    
    assert response.status_code in [200, 201]
    sale_data = response.json()
    
    installments = sale_data.get("installments", [])
    if not installments:
        # Fallback: buscar parcelas do banco
        from app.models.sale import Sale
        from app.models.installment import Installment
        sale = db.query(Sale).order_by(Sale.id.desc()).first()
        assert sale is not None
        installments = db.query(Installment).filter(Installment.sale_id == sale.id).all()
        assert len(installments) > 0, "No installments created"
        installment_id = installments[0].id
    else:
        installment_id = installments[0]["id"]
    
    # Pagar primeira parcela
    response = client.patch(
        f"/api/v1/installments/{installment_id}/pay",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"
    assert data["paid_at"] is not None


def test_list_overdue_installments(client, admin_token, test_product, test_customer, db):
    """
    Teste: Listar parcelas vencidas
    """
    from app.models.installment import Installment
    
    # Criar venda via API
    response = client.post(
        "/api/v1/sales/",
        headers=get_auth_headers(admin_token),
        json={
            "customer_id": test_customer.id,
            "payment_type": "credit",
            "installments_count": 1,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "unit_price": 50.00
                }
            ]
        }
    )
    
    assert response.status_code in [200, 201]
    sale_data = response.json()
    
    installments = sale_data.get("installments", [])
    if not installments:
        # Fallback: buscar do banco
        from app.models.sale import Sale
        sale = db.query(Sale).order_by(Sale.id.desc()).first()
        assert sale is not None
        installments = db.query(Installment).filter(Installment.sale_id == sale.id).all()
        assert len(installments) > 0
        installment_id = installments[0].id
    else:
        installment_id = installments[0]["id"]
    
    # Marcar parcela como vencida (data no passado)
    installment = db.query(Installment).filter(Installment.id == installment_id).first()
    installment.due_date = datetime.now() - timedelta(days=5)
    installment.status = "overdue"
    db.commit()
    
    # Buscar parcelas vencidas
    response = client.get(
        "/api/v1/installments/overdue",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(i["id"] == installment_id for i in data)
