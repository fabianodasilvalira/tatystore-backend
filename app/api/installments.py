from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session, require_permission
from app.schemas.installment_schemas import InstallmentPayIn
from app.services.installments_service import InstallmentsService

router = APIRouter(prefix="/installments", tags=["Installments"])

@router.put("/{id}/pay", dependencies=[Depends(require_permission("sales.create"))])
async def pay_installment(id: str, payload: InstallmentPayIn, db: AsyncSession = Depends(get_db_session)):
    svc = InstallmentsService(db)
    inst = await svc.get(id)
    if not inst:
        raise HTTPException(status_code=404, detail="Installment not found")
    await svc.mark_paid(inst)
    return inst
