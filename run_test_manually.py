import sys
from datetime import date, timedelta
# Import models FIRST to prevent ORM initialization errors
from app.models.permission import Permission
from app.models.role import Role
from app.models.company import Company
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product

from app.api.v1.endpoints.sales import create_sale
from app.schemas.sale import SaleCreate, SaleItemIn
from app.core.database import SessionLocal

# Setup DB
db = SessionLocal()

def run_debug():
    print("DEBUG MANUAL: Starting")
    try:
        # 1. Create Company
        company = db.query(Company).filter_by(document="99999999000199").first()
        if not company:
            company = Company(
                name="Debug Company",
                document="99999999000199",
                email="debug@company.com", 
                owner_id=1,
                slug="debug-company-manual"
            )
            db.add(company)
            db.commit()
            db.refresh(company)
        
        # 2. Create User
        user = db.query(User).filter_by(email="debug_user_manual@test.com").first()
        if not user:
            user = User(
                email="debug_user_manual@test.com",
                full_name="Debug User Manual",
                password_hash="hash",
                role_id=1, # Admin assuming ID 1 exists
                company_id=company.id,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 3. Create Product
        product = Product(
            name="Debug Product Manual",
            price=100.0,
            cost_price=50.0,
            stock_quantity=10,
            company_id=company.id,
            bar_code="DEBUGMANUAL123"
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # 4. Create Complete Customer
        customer = Customer(
            name="Debug Customer Manual",
            cpf="12345678901",
            phone="11999999999",
            address="Debug Address Manual",
            email="debug_manual@customer.com",
            company_id=company.id,
            is_active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 5. Create Sale
        sale_data = SaleCreate(
            customer_id=customer.id,
            items=[
                SaleItemIn(
                    product_id=product.id,
                    quantity=1,
                    unit_price=100.0
                )
            ],
            payment_type="credit",
            installments_count=3,
            first_due_date=date.today() + timedelta(days=30),
            discount_amount=0
        )

        print("DEBUG MANUAL: Calling create_sale...")
        sale = create_sale(sale_data, current_user=user, db=db)
        print(f"DEBUG MANUAL: Sale created successfully! ID: {sale.id}")
        print(f"DEBUG MANUAL: Payment Type: {sale.payment_type}")
        print(f"DEBUG MANUAL: Total Amount: {sale.total_amount}")
        
    except Exception as e:
        print(f"DEBUG MANUAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_debug()
