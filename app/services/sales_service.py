from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone, date
from app.models.product import Product
from app.models.sale import Sale, SaleItem, Installment
from app.models.customer import Customer

class SalesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: str) -> Sale | None:
        stmt = select(Sale).options(
            joinedload(Sale.items),
            joinedload(Sale.installments)
        ).where(Sale.id == id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list(self, **filters):
        stmt = select(Sale).options(joinedload(Sale.customer)).order_by(Sale.sale_date.desc())
        if (v := filters.get("customer_id")):
            stmt = stmt.where(Sale.customer_id == v)
        if (v := filters.get("status")):
            stmt = stmt.where(Sale.status == v)
        if (v := filters.get("payment_method")):
            stmt = stmt.where(Sale.payment_method == v)
        if (v := filters.get("date_from")):
            stmt = stmt.where(Sale.sale_date >= v)
        if (v := filters.get("date_to")):
            stmt = stmt.where(Sale.sale_date < v)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_sale(self, payload: dict) -> Sale:
        customer = await self.db.get(Customer, payload["customer_id"])
        if not customer:
            raise ValueError("Customer not found")

        items_in = payload["items"]
        product_ids = [str(i["product_id"]) for i in items_in]
        stmt = select(Product).where(Product.id.in_(product_ids)).with_for_update()
        products = (await self.db.execute(stmt)).scalars().all()
        if len(products) != len(product_ids):
            raise ValueError("One or more products not found")

        products_by_id = {str(p.id): p for p in products}
        sale_items: list[SaleItem] = []
        total_amount = 0.0
        for it in items_in:
            pid = str(it["product_id"]); qty = int(it["quantity"])
            p = products_by_id[pid]
            if p.stock < qty:
                raise ValueError(f"Insufficient stock for product {p.name}")
            unit_price = float(p.price or 0)
            total_amount += unit_price * qty
            sale_items.append(SaleItem(product_id=p.id, quantity=qty, unit_price=unit_price))

        sale = Sale(
            customer_id=customer.id,
            total_amount=total_amount,
            payment_method=payload["payment_method"],
            sale_date=datetime.now(timezone.utc),
            first_due_date=payload.get("first_due_date"),
            status="completed",
        )
        self.db.add(sale)
        await self.db.flush()

        for si in sale_items:
            si.sale_id = sale.id
            self.db.add(si)
            products_by_id[str(si.product_id)].stock -= si.quantity

        if sale.payment_method == "credit":
            n = payload.get("num_installments") or 1
            if n < 1: n = 1
            first_due: date | None = payload.get("first_due_date")
            if not first_due:
                raise ValueError("first_due_date required for credit")
            base = round(total_amount / n, 2)
            amounts = [base] * n
            diff = round(total_amount - base * n, 2)
            if diff != 0:
                amounts[-1] = round(amounts[-1] + diff, 2)
            for i in range(n):
                from datetime import timedelta
                due = first_due + timedelta(days=30*i)
                self.db.add(Installment(sale_id=sale.id, amount=amounts[i], due_date=due, status="pending"))

        await self.db.commit()
        await self.db.refresh(sale)
        return sale

    async def cancel(self, sale: Sale):
        if sale.status != "completed":
            return sale
        for it in sale.items:
            p = await self.db.get(Product, it.product_id)
            p.stock += it.quantity
        sale.status = "canceled"
        await self.db.commit()
        await self.db.refresh(sale)
        return sale
