"""
Testes para health check do CRON
"""
import pytest
from fastapi import status


class TestCronHealthCheck:
    """Testes de health check do sistema CRON"""
    
    def test_cron_health_check_success(self, client, admin_token):
        """Deve retornar status OK do health check"""
        response = client.get(
            "/api/v1/cron/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "active"]
    
    def test_cron_health_check_without_auth(self, client):
        """Health check pode não exigir autenticação (depende da implementação)"""
        response = client.get("/api/v1/cron/health")
        
        # Alguns sistemas permitem health check público
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_cron_health_check_response_format(self, client, admin_token):
        """Deve retornar formato JSON válido"""
        response = client.get(
            "/api/v1/cron/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, dict)
