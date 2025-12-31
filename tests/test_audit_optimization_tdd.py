import pytest
from fastapi import status
from datetime import date, timedelta
from app.models.installment import Installment, InstallmentStatus
from app.models.product import Product
from app.models.customer import Customer
from app.models.sale import Sale

def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

class TestAuditOptimizationTDD:
    """
    Suíte de testes para validar as alterações da Auditoria de Rotas.
    Garante que a segurança, performance e dinamismo dos dados foram mantidos.
    """

    def test_dynamic_roles_endpoint(self, client, admin_token, test_roles):
        """Valida que o endpoint de roles retorna dados dinâmicos do banco"""
        response = client.get(
            "/api/v1/users/roles/",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) >= 3
        role_names = [role["name"] for role in data]
        assert "Administrador" in role_names
        assert "Gerente" in role_names
        assert "usuario" in role_names

    def test_mark_overdue_security_and_isolation(self, client, manager_token, test_company1, test_company2, test_admin_user, db):
        """Valida que o novo endpoint de mark-overdue é seguro e isolado por empresa"""
        
        # Criar clientes reais
        cust1 = Customer(name="Cliente 1", email="c1@t.com", company_id=test_company1.id)
        cust2 = Customer(name="Cliente 2", email="c2@t.com", company_id=test_company2.id)
        db.add_all([cust1, cust2])
        db.commit()

        # Criar vendas reais (incluindo user_id obrigatório)
        s1 = Sale(customer_id=cust1.id, company_id=test_company1.id, user_id=test_admin_user.id, total_amount=100.0, payment_type="credit")
        s2 = Sale(customer_id=cust2.id, company_id=test_company2.id, user_id=test_admin_user.id, total_amount=200.0, payment_type="credit")
        db.add_all([s1, s2])
        db.commit()

        # 1. Criar parcela vencida na Empresa 1
        inst1 = Installment(
            sale_id=s1.id,
            company_id=test_company1.id,
            customer_id=cust1.id,
            installment_number=1,
            amount=100.0,
            due_date=date.today() - timedelta(days=5),
            status=InstallmentStatus.PENDING
        )
        
        # 2. Criar parcela vencida na Empresa 2
        inst2 = Installment(
            sale_id=s2.id,
            company_id=test_company2.id,
            customer_id=cust2.id,
            installment_number=1,
            amount=200.0,
            due_date=date.today() - timedelta(days=10),
            status=InstallmentStatus.PENDING
        )
        
        db.add_all([inst1, inst2])
        db.commit()
        
        # 3. Executar mark-overdue usando token do Gerente da Empresa 1
        response = client.post(
            "/api/v1/installments/mark-overdue",
            headers=get_auth_headers(manager_token)
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 1
        
        # 4. Verificar no banco: Apenas inst1 deve estar OVERDUE
        db.refresh(inst1)
        db.refresh(inst2)
        assert inst1.status == InstallmentStatus.OVERDUE
        assert inst2.status == InstallmentStatus.PENDING

    def test_dashboard_reports_accuracy(self, client, admin_token, test_company1, test_customer, test_admin_user, db):
        """Valida os endpoints otimizados consumidos pelo Dashboard"""
        
        from app.models.category import Category
        cat = Category(name="Teste", company_id=test_company1.id)
        db.add(cat)
        db.commit()

        # Criar venda para a parcela
        s_dash = Sale(customer_id=test_customer.id, company_id=test_company1.id, user_id=test_admin_user.id, total_amount=50.0, payment_type="credit")
        db.add(s_dash)
        db.commit()

        # Criar cliente com parcela em atraso
        inst = Installment(
            sale_id=s_dash.id,
            company_id=test_company1.id,
            customer_id=test_customer.id,
            installment_number=1,
            amount=50.0,
            due_date=date.today() - timedelta(days=2),
            status=InstallmentStatus.OVERDUE
        )
        
        # Criar produto com estoque baixo
        prod = Product(
            name="Produto Baixo Estoque",
            brand="Teste",
            company_id=test_company1.id,
            stock_quantity=2,
            min_stock=5,
            sale_price=10.0,
            cost_price=5.0,
            category_id=cat.id
        )
        
        db.add_all([inst, prod])
        db.commit()
        
        # Testar Overdue Customers
        res_overdue = client.get(
            "/api/v1/reports/overdue-customers",
            headers=get_auth_headers(admin_token)
        )
        assert res_overdue.status_code == 200
        overdue_data = res_overdue.json()
        assert "customers" in overdue_data
        assert len(overdue_data["customers"]) > 0
        
        # Testar Low Stock
        res_stock = client.get(
            "/api/v1/reports/low-stock?threshold=5",
            headers=get_auth_headers(admin_token)
        )
        assert res_stock.status_code == 200
        stock_data = res_stock.json()
        assert "items" in stock_data
        assert len(stock_data["items"]) > 0

    def test_canceled_sales_report_integrity(self, client, admin_token, db):
        """Valida que o relatório de vendas canceladas fornece dados completos"""
        # Apenas verificar se o endpoint responde corretamente
        res = client.get(
            "/api/v1/reports/canceled-sales",
            headers=get_auth_headers(admin_token)
        )
        assert res.status_code == 200
        data = res.json()
        assert "sales" in data
        assert "canceled_count" in data
