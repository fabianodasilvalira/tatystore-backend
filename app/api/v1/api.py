"""
API v1 Router
Agregador de todos os endpoints da aplicação
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    companies,
    users,
    products,
    products_import,
    customers,
    sales,
    installments,
    installment_payments,
    reports,
    pix,
    public,
    cron,
    categories
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(public.router, prefix="/public", tags=["Público"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(products_import.router, prefix="/products-import", tags=["Produtos - Importação"])
api_router.include_router(products.router, prefix="/products", tags=["Produtos"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categorias"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(sales.router, prefix="/sales", tags=["Vendas"])
api_router.include_router(installments.router, prefix="/installments", tags=["Parcelas"])
api_router.include_router(installment_payments.router, prefix="/installment-payments", tags=["Pagamentos de Parcelas"])
api_router.include_router(reports.router, prefix="/reports", tags=["Relatórios"])
api_router.include_router(pix.router, prefix="/pix", tags=["PIX"])
api_router.include_router(cron.router, prefix="/cron", tags=["Cron"])
