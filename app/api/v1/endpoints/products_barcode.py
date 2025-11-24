"""
Endpoints de Busca de Produtos por Código de Barras
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductResponse

router = APIRouter()


@router.get("/search-by-barcode", summary="Buscar produto por código de barras")
def search_product_by_barcode(
    barcode: str = Query(..., description="Código de barras do produto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Buscar Produto por Código de Barras**
    
    Busca um produto específico pelo código de barras.
    Útil para sistemas de PDV e leitores de código de barras.
    
    **Isolamento:** Apenas produtos da mesma empresa
    
    **Parâmetros:**
    - `barcode`: Código de barras do produto (obrigatório)
    
    **Retorna:** 
    - Produto encontrado com todos os detalhes
    - 404 se não encontrado
    
    **Exemplo:** GET /products/search-by-barcode?barcode=7891234567890
    """
    product = db.query(Product).filter(
        Product.barcode == barcode,
        Product.company_id == current_user.company_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return ProductResponse.model_validate(product).model_dump()


@router.get("/barcode/{barcode}", summary="Buscar produto por código de barras (rota alternativa)")
def get_product_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Buscar Produto por Código de Barras (Rota Alternativa)**
    
    Mesma funcionalidade do /search-by-barcode, mas com sintaxe de path parameter.
    
    **Isolamento:** Apenas produtos da mesma empresa
    
    **Exemplo:** GET /products/barcode/7891234567890
    """
    product = db.query(Product).filter(
        Product.barcode == barcode,
        Product.company_id == current_user.company_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return ProductResponse.model_validate(product).model_dump()
