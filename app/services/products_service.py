from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, asc, desc
from app.models.product import Product
class ProductsService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db=db; self.company_id=company_id
    async def create(self, data: dict) -> Product:
        data["company_id"]=self.company_id
        obj=Product(**data); self.db.add(obj); await self.db.commit(); await self.db.refresh(obj); return obj
    async def get(self, id: str) -> Product|None:
        stmt=select(Product).where(Product.id==id, Product.company_id==self.company_id)
        return (await self.db.execute(stmt)).scalars().first()
    async def list(self, status: str|None, q: str|None, skip:int, limit:int, order_by:str, order:str):
        stmt=select(Product).where(Product.company_id==self.company_id)
        if status: stmt=stmt.where(Product.status==status)
        if q: stmt=stmt.where(or_(Product.name.ilike(f"%{q}%"), Product.brand.ilike(f"%{q}%")))
        order_col=getattr(Product, order_by if order_by in {"name","created_at","updated_at"} else "created_at")
        stmt=stmt.order_by(asc(order_col) if order=="asc" else desc(order_col)).offset(skip).limit(limit)
        return (await self.db.execute(stmt)).scalars().all()
    async def update(self, obj: Product, data: dict) -> Product:
        for k,v in data.items():
            if v is not None and k!="company_id": setattr(obj,k,v)
        await self.db.commit(); await self.db.refresh(obj); return obj
    async def delete(self, obj: Product):
        await self.db.delete(obj); await self.db.commit()
    async def update_photo(self, obj: Product, url: str):
        obj.photo_url=url; await self.db.commit(); await self.db.refresh(obj); return obj
