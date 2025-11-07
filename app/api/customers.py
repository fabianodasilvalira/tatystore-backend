from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session, require_permission
from app.schemas.customer_schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.services.customers_service import CustomersService

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("/", response_model=CustomerOut, status_code=201, dependencies=[Depends(require_permission("products.manage"))])
async def create_customer(payload: CustomerCreate, db: AsyncSession = Depends(get_db_session)):
    svc = CustomersService(db)
    obj = await svc.create(payload.model_dump())
    return obj

@router.get("/", response_model=list[CustomerOut], dependencies=[Depends(require_permission("products.view"))])
async def list_customers(
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    svc = CustomersService(db)
    rows = await svc.list(status, q, skip, limit)
    return rows

@router.get("/{id}", response_model=CustomerOut, dependencies=[Depends(require_permission("products.view"))])
async def get_customer(id: str, db: AsyncSession = Depends(get_db_session)):
    svc = CustomersService(db)
    obj = await svc.get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return obj

@router.put("/{id}", response_model=CustomerOut, dependencies=[Depends(require_permission("products.manage"))])
async def update_customer(id: str, payload: CustomerUpdate, db: AsyncSession = Depends(get_db_session)):
    svc = CustomersService(db)
    obj = await svc.get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    for k,v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit(); await db.refresh(obj)
    return obj
