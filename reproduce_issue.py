from app.schemas.sale import SaleCreate, SaleItemIn
from datetime import date

try:
    print("Attempting to instantiate SaleCreate...")
    s = SaleCreate(
        customer_id=1,
        items=[SaleItemIn(product_id=1, quantity=1, unit_price=10.0)],
        payment_type="credit",
        first_due_date=date.today(),
        installments_count=1
    )
    print(f"Instantiation successful.")
    print(f"Keys in dict: {s.model_dump()}")
    print(f"Has attribute first_due_date? {hasattr(s, 'first_due_date')}")
    print(f"Value of first_due_date: {s.first_due_date}")
    
except Exception as e:
    print(f"Caught exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
