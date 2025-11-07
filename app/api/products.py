from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_company_id_from_path, require_permission
from app.schemas.product_schemas import ProductCreate, ProductUpdate, ProductOut
from app.services.products_service import ProductsService
from app.core.db import get_db
from app.core.storage_local import save_company_file
from app.middleware.rate_limit import limiter
router = APIRouter(prefix="/{company_slug}/api/v1/products", tags=["Products"])
@router.post("/", response_model=ProductOut, status_code=201, dependencies=[Depends(require_permission("products.create"))])
@limiter.limit("200/minute")
async def create_product(company_id: str = Depends(get_company_id_from_path), payload: ProductCreate = None, db: AsyncSession = Depends(get_db)):
    svc = ProductsService(db, company_id); return await svc.create(payload.model_dump())
@router.get("/", response_model=list[ProductOut], dependencies=[Depends(require_permission("products.view"))])
@limiter.limit("200/minute")
async def list_products(company_id: str = Depends(get_company_id_from_path), status: str | None = Query(default=None, pattern="^(active|inactive)$"),
                        q: str | None = None, skip: int = 0, limit: int = 50, order_by: str = "created_at", order: str = Query(default="desc", pattern="^(asc|desc)$"),
                        db: AsyncSession = Depends(get_db)):
    svc = ProductsService(db, company_id); return await svc.list(status, q, skip, limit, order_by, order)
@router.get("/{id}", response_model=ProductOut, dependencies=[Depends(require_permission("products.view"))])
@limiter.limit("200/minute")
async def get_product(company_id: str = Depends(get_company_id_from_path), id: str = "", db: AsyncSession = Depends(get_db)):
    svc = ProductsService(db, company_id); obj = await svc.get(id)
    if not obj: raise HTTPException(status_code=404, detail="Not Found")
    return obj
@router.put("/{id}", response_model=ProductOut, dependencies=[Depends(require_permission("products.update"))])
@limiter.limit("100/minute")
async def update_product(company_id: str = Depends(get_company_id_from_path), id: str = "", payload: ProductUpdate = None, db: AsyncSession = Depends(get_db)):
    svc = ProductsService(db, company_id); obj = await svc.get(id)
    if not obj: raise HTTPException(status_code=404, detail="Not Found")
    return await svc.update(obj, payload.model_dump(exclude_unset=True))
@router.post("/{id}/upload-photo", dependencies=[Depends(require_permission("products.update"))])
@limiter.limit("60/minute")
async def upload_photo(company_slug: str, company_id: str = Depends(get_company_id_from_path), id: str = "", file: UploadFile = None, db: AsyncSession = Depends(get_db)):
    svc = ProductsService(db, company_id); obj = await svc.get(id)
    if not obj: raise HTTPException(status_code=404, detail="Not Found")
    data = await file.read()
    url = save_company_file(company_slug, "products", file.filename, data)
    return await svc.update_photo(obj, url)

