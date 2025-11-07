from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_company_id_from_path, require_permission
from app.schemas.customer_schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.services.customers_service import CustomersService
from app.core.db import get_db
from app.core.storage_local import save_company_file
from app.middleware.rate_limit import limiter
router = APIRouter(prefix="/{company_slug}/api/v1/customers", tags=["Customers"])
@router.post("/", response_model=CustomerOut, status_code=201, dependencies=[Depends(require_permission("customers.create"))])
@limiter.limit("120/minute")
async def create_customer(company_id: str = Depends(get_company_id_from_path), payload: CustomerCreate = None, db: AsyncSession = Depends(get_db)):
    svc = CustomersService(db, company_id); return await svc.create(payload.model_dump())
@router.get("/", response_model=list[CustomerOut], dependencies=[Depends(require_permission("customers.view"))])
@limiter.limit("200/minute")
async def list_customers(company_id: str = Depends(get_company_id_from_path), status: str | None = Query(default=None, pattern="^(active|inactive)$"),
                         q: str | None = None, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    svc = CustomersService(db, company_id); return await svc.list(status, q, skip, limit)
@router.get("/{id}", response_model=CustomerOut, dependencies=[Depends(require_permission("customers.view"))])
@limiter.limit("200/minute")
async def get_customer(company_id: str = Depends(get_company_id_from_path), id: str = "", db: AsyncSession = Depends(get_db)):
    svc = CustomersService(db, company_id); obj = await svc.get(id)
    if not obj: raise HTTPException(status_code=404, detail="Not Found")
    return obj
@router.put("/{id}", response_model=CustomerOut, dependencies=[Depends(require_permission("customers.update"))])
@limiter.limit("100/minute")
async def update_customer(company_id: str = Depends(get_company_id_from_path), id: str = "", payload: CustomerUpdate = None, db: AsyncSession = Depends(get_db)):
    svc = CustomersService(db, company_id); obj = await svc.get(id)
    if not obj: raise HTTPException(status_code=404, detail="Not Found")
    data = payload.model_dump(exclude_unset=True)
    for k,v in data.items(): setattr(obj, k, v)
    await db.commit(); await db.refresh(obj); return obj
@router.post("/{id}/upload-photo", dependencies=[Depends(require_permission("customers.update"))])
@limiter.limit("60/minute")
async def upload_customer_photo(company_slug: str, company_id: str = Depends(get_company_id_from_path), id: str = "", file: UploadFile = None, db: AsyncSession = Depends(get_db)):
    data = await file.read()
    url = save_company_file(company_slug, "customers", file.filename, data)
    return {"url": url}

