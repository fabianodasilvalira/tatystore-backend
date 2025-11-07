from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sale import Installment

class InstallmentsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: str) -> Installment | None:
        return await self.db.get(Installment, id)

    async def mark_paid(self, inst: Installment):
        inst.status = "paid"
        await self.db.commit()
        return inst
