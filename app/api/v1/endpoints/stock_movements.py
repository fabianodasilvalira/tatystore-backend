"""
Endpoints de Movimentações de Estoque
Consulta histórico de auditoria de estoque
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.product import Product
from app.models.stock_movement import StockMovement

router = APIRouter()


@router.get("/products/{product_id}/movements", summary="Histórico de movimentações de estoque")
def get_product_stock_movements(
    product_id: int,
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(50, ge=1, le=100, description="Quantidade de registros (máximo 100)"),
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico completo de movimentações de estoque de um produto.
    Útil para auditoria e rastreamento de alterações.
    """
    # Verificar se produto existe e pertence à empresa
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == current_user.company_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # Buscar movimentações
    query = db.query(StockMovement).filter(
        StockMovement.product_id == product_id,
        StockMovement.company_id == current_user.company_id
    ).order_by(StockMovement.created_at.desc())
    
    total = query.count()
    movements = query.offset(skip).limit(limit).all()
    
    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "current_stock": product.stock_quantity
        },
        "total": total,
        "movements": movements,
        "metadata": {
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }
    }
