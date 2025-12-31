import sys
import os

# Force unbuffered output so we see everything immediately
sys.stdout.reconfigure(line_buffering=True)

print("VERIFY: Starting verification script...")

try:
    print("VERIFY: Importing app.main to force correct initialization...")
    import app.main 
    from datetime import date, timedelta
    
    print("VERIFY: Importing create_sale...")
    from app.api.v1.endpoints.sales import create_sale
    from app.schemas.sale import SaleCreate, SaleItemIn
    from app.core.database import SessionLocal
    
    # Import models only as needed
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.company import Company
    
    print("VERIFY: Imports successful!")
except Exception as e:
    print(f"VERIFY: Critical Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def run_verify():
    db = SessionLocal()
    try:
        print("VERIFY: Setting up DB session...")
        
        # 1. Fetch or Create Prerequisites (Safe approach)
        # Find a user that belongs to a company (not Super Admin)
        user = db.query(User).filter(User.company_id.isnot(None)).first()
        if not user:
            print("VERIFY: No suitable user found! Creating one if needed could be complex. Aborting.")
            return
            
        company = db.query(Company).filter(Company.id == user.company_id).first()
        customer = db.query(Customer).filter(Customer.company_id == company.id).first()
        product = db.query(Product).filter(Product.company_id == company.id).first()
        
        if not customer or not product:
            print("VERIFY: Missing customer or product for test.")
            return

        print(f"VERIFY: Using User ID {user.id}, Customer ID {customer.id}, Product ID {product.id}")

        # 2. Prepare Sale Data with first_due_date
        print("VERIFY: Preparing SaleCreate payload...")
        sale_data = SaleCreate(
            customer_id=customer.id,
            items=[
                SaleItemIn(
                    product_id=product.id,
                    quantity=1,
                    unit_price=10.0
                )
            ],
            payment_type="credit",
            installments_count=3,
            first_due_date=date.today() + timedelta(days=30),
            discount_amount=0
        )
        print(f"VERIFY: Payload created. first_due_date={sale_data.first_due_date}")

        # 3. Call create_sale
        print("VERIFY: Calling create_sale()...")
        sale = create_sale(sale_data, current_user=user, db=db)
        
        print("-" * 50)
        print("VERIFY: SUCCESS! Sale created.")
        print(f"VERIFY: Sale ID: {sale.id}")
        print(f"VERIFY: Total Amount: {sale.total_amount}")
        print(f"VERIFY: Installments: {len(sale.installments)}")
        print("-" * 50)
        
    except Exception as e:
        print(f"VERIFY: Runtime Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_verify()
