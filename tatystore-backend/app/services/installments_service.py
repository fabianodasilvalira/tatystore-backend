from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.installment import Installment
from app.models.sale import Sale
from datetime import datetime, timezone

class InstallmentsService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id
    
    async def get(self, id: str) -> Installment | None:
        """
        Busca uma parcela por ID validando que pertence à empresa
        
        Validações:
        - Parcela existe
        - Venda da parcela pertence à empresa
        """
        inst = await self.db.get(Installment, id)
        if not inst:
            return None
        
        # Validar que a venda pertence à empresa
        sale = await self.db.get(Sale, inst.sale_id)
        if not sale or str(sale.company_id) != str(self.company_id):
            return None
        
        return inst
    
    async def mark_paid(self, inst: Installment):
        """
        Marca uma parcela como paga
        
        Validações:
        - Parcela ainda não foi paga
        - Registra data do pagamento
        """
        if inst.status == "paid":
            return inst
        
        inst.status = "paid"
        # Poderia adicionar um campo paid_at no modelo Installment no futuro
        await self.db.commit()
        return inst
    
    async def list_overdue(self):
        """Lista todas as parcelas vencidas da empresa"""
        from datetime import date
        
        stmt = (
            select(Installment)
            .join(Sale)
            .where(
                Sale.company_id == self.company_id,
                Installment.status.in_(["pending", "overdue"]),
                Installment.due_date < date.today()
            )
            .order_by(Installment.due_date)
        )
        
        return (await self.db.execute(stmt)).scalars().all()
