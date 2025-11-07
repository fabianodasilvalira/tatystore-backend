from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.customer import Customer
class CustomersService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db=db; self.company_id=company_id
    async def create(self, data: dict) -> Customer:
        data["company_id"]=self.company_id
        obj=Customer(**data); self.db.add(obj); await self.db.commit(); await self.db.refresh(obj); return obj
    async def get(self, id: str) -> Customer|None:
        stmt=select(Customer).where(Customer.id==id, Customer.company_id==self.company_id)
        return (await self.db.execute(stmt)).scalars().first()
    async def list(self, status: str|None, q: str|None, skip:int, limit:int):
        stmt=select(Customer).where(Customer.company_id==self.company_id)
        if status: stmt=stmt.where(Customer.status==status)
        if q: stmt=stmt.where(or_(Customer.name.ilike(f"%{q}%"), Customer.cpf.ilike(f"%{q}%")))
        stmt=stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        return (await self.db.execute(stmt)).scalars().all()

