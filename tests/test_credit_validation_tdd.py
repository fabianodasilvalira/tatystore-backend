
import sys
import unittest
from unittest.mock import MagicMock
from pydantic import BaseModel
from datetime import date

# --- MOCK SETUP (Must be before imports of app code) ---
def setup_mocks():
    print("DEBUG: Setting up mocks...")
    modules_to_patch = [
        'app.models.role', 'app.models.permission', 'app.models.company',
        'app.models.sale', 'app.models.customer', 'app.models.user',
        'app.models.product', 'app.models.installment', 'app.models.stock_movement',
        'app.core.deps'
    ]
    for mod in modules_to_patch:
        if mod in sys.modules:
            del sys.modules[mod]

    # Models
    sys.modules['app.models.role'] = MagicMock()
    sys.modules['app.models.permission'] = MagicMock()
    sys.modules['app.models.company'] = MagicMock()
    sys.modules['app.models.sale'] = MagicMock()
    sys.modules['app.models.customer'] = MagicMock()
    sys.modules['app.models.product'] = MagicMock()
    sys.modules['app.models.stock_movement'] = MagicMock()
    sys.modules['app.core.deps'] = MagicMock()

    # User Model (Pydantic-friendly)
    class User(BaseModel):
        id: int
        company_id: int
        is_active: bool = True
        email: str = "test@example.com"
        model_config = {"arbitrary_types_allowed": True}

    m_user = MagicMock()
    m_user.User = User
    sys.modules['app.models.user'] = m_user

    # Installment Status
    m_inst = MagicMock()
    m_inst.InstallmentStatus.PENDING = "PENDING"
    sys.modules['app.models.installment'] = m_inst

# Apply mocks immediately
setup_mocks()

# --- IMPORTS ---
# Now it is safe to import app logic
from fastapi import HTTPException
from app.schemas.sale import SaleCreate, SaleItemIn
from app.api.v1.endpoints.sales import create_sale

# --- TEST CASE ---
class TestCreditValidation(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock()
        # Helper: User
        UserClass = sys.modules['app.models.user'].User
        self.test_user = UserClass(id=1, company_id=1)
        
        # Helper: Product
        self.mock_product = MagicMock()
        self.mock_product.id = 1
        self.mock_product.stock_quantity = 100
        self.mock_product.price = 100.0
        self.mock_product.is_active = True
        self.mock_product.cost_price = 50.0
        self.mock_product.company_id = 1
        
        # Helper: Customer Class (Mock)
        self.mock_customer = MagicMock()
        self.mock_customer.id = 1
        self.mock_customer.cpf = "123"
        self.mock_customer.phone = "123"
        self.mock_customer.address = "Addr"
        self.mock_customer.is_active = True
        self.mock_customer.company_id = 1

    def _setup_query(self, customer_obj):
        def query_side_effect(model_class):
            m = MagicMock()
            s_model = str(model_class)
            if 'Customer' in s_model:
                m.filter.return_value.with_for_update.return_value.first.return_value = customer_obj
                m.filter.return_value.first.return_value = customer_obj
            elif 'Product' in s_model:
                m.filter.return_value.with_for_update.return_value.first.return_value = self.mock_product
                m.filter.return_value.first.return_value = self.mock_product
            else:
                m.filter.return_value.first.return_value = None
            return m
        self.mock_db.query.side_effect = query_side_effect

    def test_complete_credit_sale_success(self):
        self._setup_query(self.mock_customer)
        
        sale_data = SaleCreate(
            customer_id=1,
            items=[SaleItemIn(product_id=1, quantity=1, unit_price=10.0)],
            payment_type="credit",
            installments_count=2,
            discount_amount=0
        )
        
        result = create_sale(sale_data, current_user=self.test_user, db=self.mock_db)
        self.assertEqual(result.payment_type, "credit")
        self.assertTrue(self.mock_db.commit.called)

    def test_incomplete_credit_sale_failure(self):
        self.mock_customer.cpf = None # Missing
        self._setup_query(self.mock_customer)
        
        sale_data = SaleCreate(
            customer_id=1,
            items=[SaleItemIn(product_id=1, quantity=1, unit_price=10.0)],
            payment_type="credit",
            installments_count=2,
            discount_amount=0
        )
        
        with self.assertRaises(HTTPException) as cm:
            create_sale(sale_data, current_user=self.test_user, db=self.mock_db)
        
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("CPF", cm.exception.detail)

    def test_incomplete_cash_sale_success(self):
        self.mock_customer.cpf = None # Missing but allowed for cash
        self._setup_query(self.mock_customer)
        
        sale_data = SaleCreate(
            customer_id=1,
            items=[SaleItemIn(product_id=1, quantity=1, unit_price=10.0)],
            payment_type="cash",
            discount_amount=0
        )
        
        result = create_sale(sale_data, current_user=self.test_user, db=self.mock_db)
        self.assertEqual(result.payment_type, "cash")

if __name__ == '__main__':
    unittest.main()
