from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session, require_permission
from app.schemas.product_schemas import ProductCreate, ProductUpdate, ProductOut
from app.services.products_service import ProductsService

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductOut, status_code=201, dependencies=[Depends(require_permission("products.manage"))])
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db_session)):
    svc = ProductsService(db)
    obj = await svc.create(payload.model_dump())
    return obj

@router.get("/", response_model=list[ProductOut], dependencies=[Depends(require_permission("products.view"))])
async def list_products(
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    order_by: str = "created_at",
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ProductsService(db)
    rows = await svc.list(status, q, skip, limit, order_by, order)
    return rows

@router.get("/{id}", response_model=ProductOut, dependencies=[Depends(require_permission("products.view"))])
async def get_product(id: str, db: AsyncSession = Depends(get_db_session)):
    svc = ProductsService(db)
    obj = await svc.get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@router.put("/{id}", response_model=ProductOut, dependencies=[Depends(require_permission("products.manage"))])
async def update_product(id: str, payload: ProductUpdate, db: AsyncSession = Depends(get_db_session)):
    svc = ProductsService(db)
    obj = await svc.get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    obj = await svc.update(obj, payload.model_dump(exclude_unset=True))
    return obj

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_permission("products.manage"))])
async def delete_product(id: str, db: AsyncSession = Depends(get_db_session)):
    svc = ProductsService(db)
    obj = await svc.get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    await svc.delete(obj)
    return None
