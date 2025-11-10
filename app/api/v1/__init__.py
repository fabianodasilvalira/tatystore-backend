"""
API v1 Router
Agregador de todos os endpoints da aplicação
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.endpoints import (
    auth,
    companies,
    users,
    products,
    customers,
    sales,
    installments,
    reports,
    pix,
    public,
    cron
)
from app.core.database import get_db
from app.models.company import Company
from app.models.product import Product
from app.schemas.product import ProductPublicResponse

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(products.router, prefix="/products", tags=["Produtos"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(sales.router, prefix="/sales", tags=["Vendas"])
api_router.include_router(installments.router, prefix="/installments", tags=["Parcelas"])
api_router.include_router(reports.router, prefix="/reports", tags=["Relatórios"])
api_router.include_router(pix.router, prefix="/pix", tags=["PIX"])
api_router.include_router(public.router, prefix="/public", tags=["Público"])
api_router.include_router(cron.router, prefix="/cron", tags=["Cron"])


@api_router.get("/empresa/{slug}", response_model=List[ProductPublicResponse], tags=["Loja Pública"], summary="[PÚBLICO] Vitrine da Empresa")
def get_store_products(
    slug: str,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    **[ENDPOINT PÚBLICO] Vitrine da Empresa**
    
    Lista produtos de uma empresa usando URL amigável.
    Não requer autenticação - ideal para clientes navegarem.
    
    **URL Exemplo:** `/empresa/minha-loja`
    
    **Uso:**
    1. Ao cadastrar empresa, sistema gera slug automaticamente
    2. Dono compartilha URL `/empresa/{slug}` com clientes
    3. Clientes acessam vitrine sem fazer login
    
    **Parâmetros:**
    - `slug`: Identificador único da empresa (ex: "minha-loja")
    - `search`: Buscar produtos por nome (opcional)
    - `skip`: Paginação - pular registros
    - `limit`: Quantidade de produtos (máximo: 100)
    
    **Retorna:** Lista de produtos ativos da empresa
    """
    # Buscar empresa pelo slug
    company = db.query(Company).filter(
        Company.slug == slug,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Loja '{slug}' não encontrada ou inativa"
        )
    
    # Buscar produtos ativos
    query = db.query(Product).filter(
        Product.company_id == company.id,
        Product.is_active == True
    )
    
    # Filtro de busca opcional
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Aplicar paginação
    products = query.offset(skip).limit(limit).all()
    
    return products


@api_router.get("/empresa/{slug}/produto/{product_id}", response_model=ProductPublicResponse, tags=["Loja Pública"], summary="[PÚBLICO] Detalhes do Produto")
def get_store_product_detail(
    slug: str,
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    **[ENDPOINT PÚBLICO] Detalhes do Produto**
    
    Retorna informações detalhadas de um produto específico.
    Não requer autenticação.
    
    **URL Exemplo:** `/empresa/minha-loja/produto/123`
    
    **Parâmetros:**
    - `slug`: Slug da empresa
    - `product_id`: ID do produto
    """
    # Buscar empresa
    company = db.query(Company).filter(
        Company.slug == slug,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Loja '{slug}' não encontrada"
        )
    
    # Buscar produto
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == company.id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )
    
    return product
