"""
Endpoints de Relatórios (v1)
Vendas, lucros, produtos, cancelamentos, vencidos, baixo estoque
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.product import Product
from app.models.installment import Installment, InstallmentStatus
from app.services.reports_service import ReportsService
from app.schemas.pagination import paginate

router = APIRouter()


def get_date_range(period: str, custom_date: Optional[date] = None):
    """Helper para obter range de datas baseado no período"""
    today = date.today()
    
    if period == "today":
        return today, today + timedelta(days=1)
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=7)
    elif period == "month":
        return date(today.year, today.month, 1), date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    elif period == "custom" and custom_date:
        return custom_date, custom_date + timedelta(days=1)
    else:
        return None, None


@router.get("/sales", summary="Relatório de vendas")
def report_sales(
    period: str = "month",
    custom_date: Optional[date] = None,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Relatório de Vendas**
    
    Retorna resumo de vendas por período.
    
    **Requer:** Admin ou Gerente
    
    **Períodos:**
    - `today`: Hoje
    - `week`: Semana atual
    - `month`: Mês atual
    - `custom`: Data específica (use custom_date)
    """
    start_date, end_date = get_date_range(period, custom_date)
    
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )
    
    if period == "today":
        # For today, just filter by company and non-cancelled status
        sales = db.query(Sale).filter(
            Sale.company_id == current_user.company_id,
            Sale.status != SaleStatus.CANCELLED
        ).all()
    else:
        sales = db.query(Sale).filter(
            Sale.company_id == current_user.company_id,
            Sale.created_at >= start_date,
            Sale.created_at < end_date,
            Sale.status != SaleStatus.CANCELLED
        ).all()
    
    total_revenue = sum(s.total_amount for s in sales)
    total_discount = sum(s.discount_amount for s in sales)
    count = len(sales)
    
    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_sales": count,
        "total_revenue": total_revenue,
        "total_discount": total_discount,
        "average_ticket": total_revenue / count if count > 0 else 0
    }


@router.get("/profit", summary="Relatório de lucro")
def report_profit(
    period: str = "month",
    custom_date: Optional[date] = None,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Relatório de Lucro**
    
    Retorna análise de custo vs receita por período.
    
    **Requer:** Admin ou Gerente
    """
    start_date, end_date = get_date_range(period, custom_date)
    
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )
    
    sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= start_date,
        Sale.created_at < end_date,
        Sale.status != SaleStatus.CANCELLED
    ).all()
    
    total_revenue = sum(s.total_amount for s in sales)
    total_cost = 0
    
    for sale in sales:
        for item in sale.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                total_cost += product.cost_price * item.quantity
    
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "period": period,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "profit": profit,
        "margin_percentage": margin
    }


@router.get("/sold-products", summary="Produtos mais vendidos")
def report_sold_products(
    period: str = "month",
    custom_date: Optional[date] = None,
    limit: int = 10,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Produtos Mais Vendidos**
    
    Retorna ranking de produtos por quantidade vendida.
    
    **Requer:** Admin ou Gerente
    """
    start_date, end_date = get_date_range(period, custom_date)
    
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )
    
    items = db.query(
        SaleItem.product_id,
        Product.name,
        func.sum(SaleItem.quantity).label("quantity"),
        func.sum(SaleItem.total_price).label("revenue")
    ).join(Sale, Sale.id == SaleItem.sale_id).join(
        Product, Product.id == SaleItem.product_id
    ).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= start_date,
        Sale.created_at < end_date,
        Sale.status != SaleStatus.CANCELLED
    ).group_by(SaleItem.product_id, Product.name).order_by(
        func.sum(SaleItem.quantity).desc()
    ).limit(limit).all()
    
    return {
        "period": period,
        "products": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "quantity_sold": item.quantity,
                "revenue": item.revenue
            }
            for item in items
        ]
    }


@router.get("/canceled-sales", summary="Vendas canceladas")
def report_canceled_sales(
    period: str = "month",
    custom_date: Optional[date] = None,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Vendas Canceladas**
    
    Retorna análise de vendas canceladas.
    
    **Requer:** Admin ou Gerente
    """
    start_date, end_date = get_date_range(period, custom_date)
    
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )
    
    canceled_sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= start_date,
        Sale.created_at < end_date,
        Sale.status == SaleStatus.CANCELLED
    ).all()
    
    total_lost = sum(s.total_amount for s in canceled_sales)
    
    return {
        "period": period,
        "canceled_count": len(canceled_sales),
        "total_amount": total_lost
    }


@router.get("/overdue", summary="Parcelas vencidas")
def report_overdue(
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Parcelas Vencidas**
    
    Retorna análise de parcelas em atraso.
    
    **Requer:** Admin ou Gerente
    """
    today = date.today()
    
    overdue = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.status == InstallmentStatus.OVERDUE,
        Installment.due_date < today
    ).all()
    
    total_overdue = sum(i.amount for i in overdue)
    
    return {
        "overdue_count": len(overdue),
        "total_amount": total_overdue,
        "oldest_date": min((i.due_date for i in overdue), default=None)
    }


@router.get("/low-stock", response_model=dict, summary="Produtos com baixo estoque")
def report_low_stock(
    threshold: int = 5,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Produtos com Baixo Estoque**
    
    Retorna lista de produtos abaixo do threshold.
    
    **Parâmetros:**
    - `threshold`: Quantidade mínima (padrão: 5)
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Resposta:** Dados paginados com metadados (total, página, total_pages, etc)
    """
    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.is_active == True,
        Product.stock_quantity <= threshold
    ).order_by(Product.stock_quantity.asc())
    
    total = query.count()
    
    products = query.offset(skip).limit(limit).all()
    
    result = products
    
    return paginate(result, total, skip, limit)
