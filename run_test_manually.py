import sys
import os
from datetime import date

# Ensure /app is in path
sys.path.append("/app")

print("DEBUG MANUAL: Starting")

try:
    print("DEBUG MANUAL: Importing sales endpoint...")
    from app.api.v1.endpoints.sales import create_sale
    print("DEBUG MANUAL: Import successful")
    
    from app.schemas.sale import SaleCreate, SaleItemIn
    
    print("DEBUG MANUAL: Instantiating SaleCreate...")
    s = SaleCreate(
        customer_id=1,
        items=[],
        payment_type="credit",
        first_due_date=date.today(),
        installments_count=1
    )
    print(f"DEBUG MANUAL: SaleCreate keys: {s.model_dump().keys() if hasattr(s, 'model_dump') else s.__dict__.keys()}")
    
    # Mock mocks
    class MockUser:
        id = 1
        company_id = 1
        
    class MockDB:
        def query(self, *args): return self
        def filter(self, *args): return self
        def with_for_update(self): return self
        def first(self): return None # Simulate no customer found provided id 1
        def add(self, *args): pass
        def flush(self, *args): pass
        def commit(self, *args): pass
        def refresh(self, *args): pass
        
    print("DEBUG MANUAL: Calling create_sale...")
    try:
        create_sale(s, current_user=MockUser(), db=MockDB())
    except Exception as e:
        print(f"DEBUG MANUAL: Caught exception from create_sale: {e}")

except Exception as e:
    print(f"DEBUG MANUAL: Main exception: {e}")
    import traceback
    traceback.print_exc()
