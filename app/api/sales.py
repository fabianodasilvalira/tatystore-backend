from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.api.deps import get_db_session, require_permission
from app.schemas.sale_schemas import SaleCreate, SaleOut
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("/", response_model=SaleOut, status_code=201, dependencies=[Depends(require_permission("sales.create"))])
async def create_sale(payload: SaleCreate, db: AsyncSession = Depends(get_db_session)):
    svc = SalesService(db)
    try:
        sale = await svc.create_sale(payload.model_dump())
        return sale
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[SaleOut], dependencies=[Depends(require_permission("products.view"))])
async def list_sales(
    customer_id: str | None = None,
    status: str | None = Query(default=None, pattern="^(completed|canceled)$"),
    payment_method: str | None = Query(default=None, pattern="^(cash|credit)$"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    svc = SalesService(db)
    rows = await svc.list(customer_id=customer_id, status=status, payment_method=payment_method,
                          date_from=date_from, date_to=date_to)
    return rows

@router.get("/{id}", response_model=SaleOut, dependencies=[Depends(require_permission("products.view"))])
async def get_sale(id: str, db: AsyncSession = Depends(get_db_session)):
    svc = SalesService(db)
    sale = await svc.get(id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale

@router.put("/{id}/cancel", response_model=SaleOut, dependencies=[Depends(require_permission("sales.cancel"))])
async def cancel_sale(id: str, db: AsyncSession = Depends(get_db_session)):
    svc = SalesService(db)
    sale = await svc.get(id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    sale = await svc.cancel(sale)
    return sale
