from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.models.customer import Customer
from app.models.sale import Installment, Sale

class CustomersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Customer:
        obj = Customer(**data)
        self.db.add(obj)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, id: str) -> Customer | None:
        return await self.db.get(Customer, id)

    async def list(self, status: str | None, q: str | None, skip: int, limit: int):
        stmt = select(Customer)
        if status:
            stmt = stmt.where(Customer.status == status)
        if q:
            stmt = stmt.where(or_(Customer.name.ilike(f"%{q}%"), Customer.cpf.ilike(f"%{q}%")))
        stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def debt_summary(self, customer_id: str) -> dict:
        total = (await self.db.execute(
            select(func.coalesce(func.sum(Installment.amount), 0))
            .join(Sale, Sale.id == Installment.sale_id)
            .where(Sale.customer_id == customer_id, Installment.status.in_(["pending","overdue"]))
        )).scalar_one()
        overdue_count = (await self.db.execute(
            select(func.count(Installment.id))
            .join(Sale, Sale.id == Installment.sale_id)
            .where(Sale.customer_id == customer_id, Installment.status == "overdue")
        )).scalar_one()
        return {"total_open_amount": float(total or 0), "overdue_count": int(overdue_count or 0)}
