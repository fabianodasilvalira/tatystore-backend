from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.core.deps import get_company_id_from_path, require_permission
from app.schemas.sale_schemas import SaleCreate, SaleOut
from app.services.sales_service import SalesService
from app.core.db import get_db
from app.middleware.rate_limit import limiter
router = APIRouter(prefix="/{company_slug}/api/v1/sales", tags=["Sales"])
@router.post("/", response_model=SaleOut, status_code=201, dependencies=[Depends(require_permission("sales.create"))])
@limiter.limit("120/minute")
async def create_sale(company_id: str = Depends(get_company_id_from_path), payload: SaleCreate = None, db: AsyncSession = Depends(get_db)):
    svc=SalesService(db, company_id)
    try: return await svc.create_sale(payload.model_dump())
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
@router.get("/", response_model=list[SaleOut], dependencies=[Depends(require_permission("customers.view"))])
@limiter.limit("200/minute")
async def list_sales(company_id: str = Depends(get_company_id_from_path), customer_id: str|None=None, status: str|None=Query(default=None, pattern="^(completed|canceled)$"),
                     payment_method: str|None=Query(default=None, pattern="^(cash|credit)$"), date_from: datetime|None=None, date_to: datetime|None=None,
                     db: AsyncSession = Depends(get_db)):
    svc=SalesService(db, company_id)
    return await svc.list(customer_id=customer_id, status=status, payment_method=payment_method, date_from=date_from, date_to=date_to)
@router.get("/{id}", response_model=SaleOut, dependencies=[Depends(require_permission("customers.view"))])
@limiter.limit("200/minute")
async def get_sale(company_id: str = Depends(get_company_id_from_path), id: str = "", db: AsyncSession = Depends(get_db)):
    svc=SalesService(db, company_id); sale=await svc.get(id)
    if not sale: raise HTTPException(status_code=404, detail="Not Found")
    return sale
@router.put("/{id}/cancel", response_model=SaleOut, dependencies=[Depends(require_permission("sales.cancel"))])
@limiter.limit("60/minute")
async def cancel_sale(company_id: str = Depends(get_company_id_from_path), id: str = "", db: AsyncSession = Depends(get_db)):
    svc=SalesService(db, company_id); sale=await svc.get(id)
    if not sale: raise HTTPException(status_code=404, detail="Not Found")
    return await svc.cancel(sale)

