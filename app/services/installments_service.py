from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sale import Installment, Sale
class InstallmentsService:
    def __init__(self, db: AsyncSession, company_id: str): self.db=db; self.company_id=company_id
    async def get(self, id: str) -> Installment|None:
        inst=await self.db.get(Installment, id)
        if not inst: return None
        sale=await self.db.get(Sale, inst.sale_id)
        if not sale or str(sale.company_id)!=str(self.company_id): return None
        return inst
    async def mark_paid(self, inst: Installment):
        inst.status="paid"; await self.db.commit(); return inst

