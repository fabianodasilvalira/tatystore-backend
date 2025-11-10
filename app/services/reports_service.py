from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.sale import Sale
from app.models.installment import Installment
from app.models.customer import Customer
from app.models.product import Product

class ReportsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sales_summary(self, date_from, date_to):
        # consult from materialized view for speed
        stmt = text("""
            SELECT COALESCE(SUM(total_revenue),0) AS total_revenue,
                   COALESCE(SUM(total_sales),0)   AS total_sales
            FROM sales_summary_mv
            WHERE day >= :d1 AND day < :d2
        """)
        row = (await self.db.execute(stmt, {"d1": date_from, "d2": date_to})).first()
        return {"total_revenue": float(row.total_revenue or 0), "total_sales": int(row.total_sales or 0)}

    async def overdue_customers(self):
        stmt = (
            select(
                Customer.id,
                Customer.name,
                func.coalesce(func.sum(Installment.amount), 0).label("total"),
                func.count(Installment.id).label("count"),
            )
            .join(Sale, Sale.customer_id == Customer.id)
            .join(Installment, Installment.sale_id == Sale.id)
            .where(Installment.status == "overdue")
            .group_by(Customer.id, Customer.name)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            {"customer_id": str(r.id), "name": r.name, "total_overdue_amount": float(r.total), "installments_count": int(r.count)}
            for r in rows
        ]

    async def low_stock(self, threshold: int = 5):
        stmt = select(Product).where(Product.stock <= threshold).order_by(Product.stock.asc())
        rows = (await self.db.execute(stmt)).scalars().all()
        return [{"id": str(p.id), "name": p.name, "stock": p.stock} for p in rows]
