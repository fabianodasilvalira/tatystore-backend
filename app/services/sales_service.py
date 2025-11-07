from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta, date
from app.models.product import Product
from app.models.sale import Sale, SaleItem, Installment
from app.models.customer import Customer
class SalesService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db=db; self.company_id=company_id
    async def get(self, id: str) -> Sale|None:
        stmt=select(Sale).options(joinedload(Sale.items), joinedload(Sale.installments)).where(Sale.id==id, Sale.company_id==self.company_id)
        return (await self.db.execute(stmt)).scalars().first()
    async def list(self, **filters):
        stmt=select(Sale).options(joinedload(Sale.installments)).where(Sale.company_id==self.company_id).order_by(Sale.sale_date.desc())
        if (v:=filters.get("customer_id")): stmt=stmt.where(Sale.customer_id==v)
        if (v:=filters.get("status")): stmt=stmt.where(Sale.status==v)
        if (v:=filters.get("payment_method")): stmt=stmt.where(Sale.payment_method==v)
        if (v:=filters.get("date_from")): stmt=stmt.where(Sale.sale_date>=v)
        if (v:=filters.get("date_to")): stmt=stmt.where(Sale.sale_date<v)
        return (await self.db.execute(stmt)).scalars().all()
    async def create_sale(self, payload: dict) -> Sale:
        customer=(await self.db.execute(select(Customer).where(Customer.id==payload["customer_id"], Customer.company_id==self.company_id))).scalars().first()
        if not customer: raise ValueError("Customer not found")
        product_ids=[str(i["product_id"]) for i in payload["items"]]
        products=(await self.db.execute(select(Product).where(Product.id.in_(product_ids), Product.company_id==self.company_id).with_for_update())).scalars().all()
        if len(products)!=len(product_ids): raise ValueError("Product not found or other company")
        pmap={str(p.id):p for p in products}; items=[]; total=0.0
        for it in payload["items"]:
            p=pmap[str(it["product_id"])]; qty=int(it["quantity"])
            if p.stock<qty: raise ValueError(f"Insufficient stock for product {p.name}")
            price=float(p.price or 0); total += price*qty; items.append(SaleItem(product_id=p.id, quantity=qty, unit_price=price))
        sale=Sale(company_id=self.company_id, customer_id=customer.id, total_amount=total,
                  payment_method=payload["payment_method"], sale_date=datetime.now(timezone.utc),
                  first_due_date=payload.get("first_due_date"), status="completed")
        self.db.add(sale); await self.db.flush()
        for si in items:
            si.sale_id=sale.id; self.db.add(si); pmap[str(si.product_id)].stock -= si.quantity
        if sale.payment_method=="credit":
            n=payload.get("num_installments") or 1
            if n<1: n=1
            first_due=payload.get("first_due_date")
            if not first_due: raise ValueError("first_due_date required for credit")
            base=round(total/n,2); amounts=[base]*n; diff=round(total-base*n,2)
            if diff!=0: amounts[-1]=round(amounts[-1]+diff,2)
            from datetime import timedelta
            for i in range(n):
                due = first_due + timedelta(days=30*i)
                self.db.add(Installment(sale_id=sale.id, amount=amounts[i], due_date=due, status="pending"))
        await self.db.commit(); await self.db.refresh(sale); return sale
    async def cancel(self, sale: Sale):
        if sale.status!="completed": return sale
        for it in sale.items:
            p=(await self.db.execute(select(Product).where(Product.id==it.product_id, Product.company_id==self.company_id))).scalars().first()
            if p: p.stock += it.quantity
        sale.status="canceled"; await self.db.commit(); await self.db.refresh(sale); return sale

