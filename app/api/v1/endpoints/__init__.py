"""
Endpoints da API v1
"""
from . import (
    auth,
    companies,
    users,
    products,
    customers,
    sales,
    installments,
    installment_payments,
    reports,
    pix,
    public,
    cron,
    categories,
    products_import
)

__all__ = [
    "auth",
    "companies",
    "users",
    "products",
    "customers",
    "sales",
    "installments",
    "installment_payments",
    "reports",
    "pix",
    "public",
    "cron",
    "categories",
    "products_import",
]
