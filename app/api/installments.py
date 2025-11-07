from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_company_id_from_path, require_permission
from app.schemas.installment_schemas import InstallmentPayIn
from app.services.installments_service import InstallmentsService
from app.core.db import get_db
from app.middleware.rate_limit import limiter
router = APIRouter(prefix="/{company_slug}/api/v1/installments", tags=["Installments"])
@router.put("/{id}/pay", dependencies=[Depends(require_permission("sales.create"))])
@limiter.limit("60/minute")
async def pay_installment(company_id: str = Depends(get_company_id_from_path), id: str = "", payload: InstallmentPayIn = None, db: AsyncSession = Depends(get_db)):
    svc=InstallmentsService(db, company_id)
    inst=await svc.get(id)
    if not inst: raise HTTPException(status_code=404, detail="Not Found")
    await svc.mark_paid(inst); return inst

