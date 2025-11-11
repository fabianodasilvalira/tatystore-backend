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
    cron,
    categories
)
from app.core.database import get_db
from app.models.company import Company
from app.models.product import Product
from app.schemas.product import ProductPublicResponse

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(public.router, prefix="/public", tags=["Público"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(products.router, prefix="/products", tags=["Produtos"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categorias"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(sales.router, prefix="/sales", tags=["Vendas"])
api_router.include_router(installments.router, prefix="/installments", tags=["Parcelas"])
api_router.include_router(reports.router, prefix="/reports", tags=["Relatórios"])
api_router.include_router(pix.router, prefix="/pix", tags=["PIX"])
api_router.include_router(cron.router, prefix="/cron", tags=["Cron"])

# Essas rotas já existem corretamente em public.py com prefixo /public/companies/{company_slug}/products
