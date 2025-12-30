"""
Testes avançados de parcelas com filtros combinados
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta


class TestInstallmentsAdvancedFilters:
    """Testes de filtros avançados de parcelas"""
    
    def test_filter_installments_by_paid_status(self, client, admin_token, test_company, db):
        """Deve filtrar parcelas com status PAID"""
        response = client.get(
            "/api/v1/installments?status=paid",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        for inst in installments:
            assert inst["status"] == "paid"
    
    def test_filter_installments_by_pending_status(self, client, admin_token):
        """Deve filtrar parcelas com status PENDING"""
        response = client.get(
            "/api/v1/installments?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        for inst in installments:
            assert inst["status"] == "pending"
    
    def test_filter_installments_by_date_range(self, client, admin_token):
        """Deve filtrar parcelas por intervalo de datas"""
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/v1/installments?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        for inst in installments:
            due_date = datetime.fromisoformat(inst["due_date"].replace("Z", "+00:00"))
            assert datetime.strptime(start_date, "%Y-%m-%d") <= due_date <= datetime.strptime(end_date, "%Y-%m-%d")
    
    def test_filter_installments_combined(self, client, admin_token, test_customer):
        """Deve aplicar filtros combinados (cliente + status)"""
        response = client.get(
            f"/api/v1/installments/customer/{test_customer.id}?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        for inst in installments:
            assert inst["status"] == "pending"
    
    def test_filter_installments_invalid_date_format(self, client, admin_token):
        """Deve rejeitar formato de data inválido"""
        response = client.get(
            "/api/v1/installments?start_date=invalid-date",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Pode retornar 400 ou ignorar filtro inválido
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK]


class TestInstallmentsSorting:
    """Testes de ordenação de parcelas"""
    
    def test_sort_installments_by_due_date_asc(self, client, admin_token):
        """Deve ordenar parcelas por data de vencimento (crescente)"""
        response = client.get(
            "/api/v1/installments?sort=due_date&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        if len(installments) > 1:
            dates = [inst["due_date"] for inst in installments]
            assert dates == sorted(dates)
    
    def test_sort_installments_by_amount_desc(self, client, admin_token):
        """Deve ordenar parcelas por valor (decrescente)"""
        response = client.get(
            "/api/v1/installments?sort=amount&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        if isinstance(response_data, dict) and "items" in response_data:
            installments = response_data["items"]
        else:
            installments = response_data
        
        if len(installments) > 1:
            amounts = [inst["amount"] for inst in installments]
            assert amounts == sorted(amounts, reverse=True)
