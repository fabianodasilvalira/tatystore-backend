"""
Endpoints de Relatórios (v1)
Vendas, lucros, produtos, cancelamentos, vencidos, baixo estoque
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta
from sqlalchemy import func
import calendar

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.product import Product
from app.models.installment import Installment, InstallmentStatus
from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
from app.services.reports_service import ReportsService
from app.api.v1.endpoints.installments import _calculate_installment_balance
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
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Relatório de Vendas**
    
    Retorna resumo de vendas por período.
    
    **PERMISSÃO:** Gerente, Vendedor e Admin
    
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
    
    sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at < datetime.combine(end_date, datetime.min.time()),
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


@router.get("/sales-over-time", summary="Vendas ao longo do tempo")
def report_sales_over_time(
    period: str = Query("week", pattern="^(day|week|month)$", description="Granularidade: day, week, month"),
    start_date: Optional[date] = Query(None, description="Data inicial (padrão: 30 dias atrás)"),
    end_date: Optional[date] = Query(None, description="Data final (padrão: hoje)"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Relatório de Vendas ao Longo do Tempo**
    
    Analisa tendência de vendas agregando dados por dia, semana ou mês.
    Útil para visualizar crescimento e padrões de vendas.
    
    **PERMISSÃO:** Gerente, Vendedor e Admin
    
    **Parâmetros:**
    - `period`: Granularidade de agregação
      - `day`: Dados diários
      - `week`: Dados por semana (segunda a domingo)
      - `month`: Dados por mês
    - `start_date`: Data inicial (padrão: 30 dias atrás)
    - `end_date`: Data final (padrão: hoje)
    
    **Retorna:**
    - Array com períodos e estatísticas: total_sales, total_revenue, average_ticket, completed_count
    
    **Exemplo:** GET /reports/sales-over-time?period=week&start_date=2025-01-01
    """
    today = date.today()
    
    # Definir datas padrão se não informadas
    if not end_date:
        end_date = today
    if not start_date:
        start_date = today - timedelta(days=30)
    
    # Validar datas
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data inicial não pode ser maior que data final"
        )
    
    # Buscar todas as vendas no período
    sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
        Sale.status == SaleStatus.COMPLETED
    ).all()
    
    # Agrupar por período
    period_data = {}
    
    for sale in sales:
        sale_date = sale.created_at.date()
        
        # Determinar chave de período
        if period == "day":
            period_key = sale_date
            period_label = sale_date.isoformat()
        elif period == "week":
            # Segunda de semana atual
            week_start = sale_date - timedelta(days=sale_date.weekday())
            period_key = week_start
            period_label = f"{week_start.isoformat()} a {(week_start + timedelta(days=6)).isoformat()}"
        else:  # month
            period_key = date(sale_date.year, sale_date.month, 1)
            period_label = f"{sale_date.year}-{sale_date.month:02d}"
        
        if period_key not in period_data:
            period_data[period_key] = {
                "period": period_label,
                "start_date": period_key,
                "end_date": period_key + (timedelta(days=6) if period == "week" else timedelta(days=calendar.monthrange(period_key.year, period_key.month)[1] - 1) if period == "month" else timedelta(days=0)),
                "total_sales": 0,
                "total_revenue": 0.0,
                "completed_count": 0,
                "average_ticket": 0.0
            }
        
        period_data[period_key]["total_sales"] += 1
        period_data[period_key]["total_revenue"] += sale.total_amount
        period_data[period_key]["completed_count"] += 1
    
    # Calcular ticket médio
    for period_info in period_data.values():
        if period_info["completed_count"] > 0:
            period_info["average_ticket"] = period_info["total_revenue"] / period_info["completed_count"]
    
    # Ordenar por período
    sorted_periods = sorted(period_data.items(), key=lambda x: x[0])
    result = [item[1] for item in sorted_periods]
    
    return {
        "period_type": period,
        "date_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_periods": len(result),
        "data": result
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
    
    **PERMISSÃO:** Admin e Gerente (acesso total aos dados financeiros)
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
    products_without_cost = set()  # Produtos sem preço de custo
    
    for sale in sales:
        for item in sale.items:
            # item.product.cost_price é o custo atual do produto
            cost_price = item.product.cost_price if item.product.cost_price is not None else 0.0
            
            # Registrar produtos sem preço de custo
            if cost_price == 0.0 or item.product.cost_price is None:
                products_without_cost.add((item.product.id, item.product.name))
            
            total_cost += float(cost_price) * item.quantity

    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Preparar mensagem de aviso se houver produtos sem custo
    warning = None
    if products_without_cost:
        warning = {
            "message": "Não é possível calcular o lucro com precisão. Alguns produtos vendidos não possuem preço de custo cadastrado. Para obter relatórios de lucro precisos, é necessário cadastrar o preço de compra de todos os produtos.",
            "products_count": len(products_without_cost),
            "products": [
                {"id": prod_id, "name": prod_name}
                for prod_id, prod_name in sorted(products_without_cost, key=lambda x: x[1])
            ]
        }

    return {
        "period": period,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "profit": profit,
        "margin_percentage": margin,
        "warning": warning
    }


@router.get("/sold-products", summary="Produtos mais vendidos")
def report_sold_products(
    period: str = "month",
    custom_date: Optional[date] = None,
    limit: int = 10,
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Produtos Mais Vendidos**

    Retorna ranking de produtos por quantidade vendida.

    **PERMISSÃO:** Admin, Gerente e Vendedor
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
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Vendas Canceladas**

    Retorna análise de vendas canceladas com detalhe de cada venda.

    **PERMISSÃO:** Admin, Gerente e Vendedor

    **Parâmetros:**
    - `period`: Período predefinido (today, week, month, custom)
    - `custom_date`: Data para período custom

    **Resposta:**
    - `canceled_count`: Número total de vendas canceladas
    - `total_amount`: Soma do valor total perdido
    - `sales`: Array de vendas canceladas com detalhes
      - `sale_id`: ID da venda
      - `customer_name`: Nome do cliente
      - `sale_date`: Data da venda
      - `total_amount`: Valor total da venda

    **Exemplo:** GET /reports/canceled-sales?period=month
    """
    start_date, end_date = get_date_range(period, custom_date)

    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )

    canceled_sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at < datetime.combine(end_date, datetime.min.time()),
        Sale.status == SaleStatus.CANCELLED
    ).all()

    total_lost = sum(s.total_amount for s in canceled_sales)

    # Formatar array de vendas canceladas
    sales_data = [
        {
            "sale_id": sale.id,
            "customer_name": sale.customer.name if sale.customer else "N/A",
            "sale_date": sale.created_at.isoformat(),
            "total_amount": float(sale.total_amount)
        }
        for sale in canceled_sales
    ]

    return {
        "period": period,
        "canceled_count": len(canceled_sales),
        "total_amount": round(total_lost, 2),
        "sales": sales_data
    }


@router.get("/overdue", summary="Parcelas vencidas")
def report_overdue(
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Parcelas Vencidas**

    Retorna análise de parcelas em atraso.

    **PERMISSÃO:** Admin, Gerente e Vendedor
    """
    today = date.today()

    overdue = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.status == InstallmentStatus.OVERDUE,
        Installment.due_date < today
    ).all()

    total_overdue = sum(_calculate_installment_balance(i)[1] for i in overdue)

    return {
        "overdue_count": len(overdue),
        "total_amount": total_overdue,
        "oldest_date": min((i.due_date for i in overdue), default=None)
    }


@router.get("/overdue-customers", summary="Clientes com parcelas vencidas")
def report_overdue_customers(
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Clientes com Parcelas Vencidas**
    
    Identifica todos os clientes com parcelas não pagas após a data de vencimento.
    Útil para gestão de cobrança e análise de risco de crédito.
    
    **PERMISSÃO:** Admin, Gerente e Vendedor
    
    **Resposta:**
    - `overdue_count`: Número de clientes únicos com débito
    - `total_amount`: Soma total de todas as parcelas vencidas (apenas saldo restante)
    - `oldest_date`: Data de vencimento mais antiga
    - `customers`: Array de clientes com débito
      - `id`: ID do cliente
      - `name`: Nome do cliente
      - `phone`: Telefone para contato
      - `total_debt`: Soma das parcelas vencidas deste cliente (saldo restante)
    
    **Exemplo:** GET /reports/overdue-customers
    """
    today = date.today()
    
    # Buscar todas as parcelas com status OVERDUE
    overdue_installments = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.status == InstallmentStatus.OVERDUE,
        Installment.due_date < today
    ).all()
    
    # Agrupar por cliente
    customers_debt = {}
    total_overdue_amount = 0.0
    oldest_date = None
    
    for installment in overdue_installments:
        _, remaining = _calculate_installment_balance(installment)
        total_overdue_amount += remaining
        
        # Atualizar data mais antiga
        if oldest_date is None or installment.due_date < oldest_date:
            oldest_date = installment.due_date
        
        # Agrupar por cliente
        customer_id = installment.customer_id
        if customer_id not in customers_debt:
            customers_debt[customer_id] = {
                "customer": installment.customer,
                "total_debt": 0.0
            }
        
        customers_debt[customer_id]["total_debt"] += remaining
    
    # Formatar resposta com dados de clientes
    customers_list = []
    for customer_id, debt_info in customers_debt.items():
        customer = debt_info["customer"]
        customers_list.append({
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone or "N/A",
            "total_debt": round(debt_info["total_debt"], 2)
        })
    
    # Ordenar por maior débito
    customers_list.sort(key=lambda x: x["total_debt"], reverse=True)
    
    return {
        "overdue_count": len(customers_debt),
        "total_amount": round(total_overdue_amount, 2),
        "oldest_date": oldest_date.isoformat() if oldest_date else None,
        "customers": customers_list
    }


@router.get("/low-stock", response_model=dict, summary="Produtos com baixo estoque")
def report_low_stock(
    threshold: int = 5,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Produtos com Baixo Estoque**

    Retorna lista de produtos abaixo do threshold.

    **PERMISSÃO:** Admin, Gerente e Vendedor

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

    products_data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "sku": p.sku,
            "barcode": p.barcode,
            "brand": p.brand,
            "image_url": p.image_url,
            "sale_price": float(p.sale_price),
            "cost_price": float(p.cost_price),
            "stock_quantity": p.stock_quantity,
            "min_stock": p.min_stock,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "company_id": p.company_id
        }
        for p in products
    ]

    return paginate(products_data, total, skip, limit)


@router.get("/sales-summary", summary="Resumo de vendas com lucro")
def report_sales_summary(
    period: str = Query("month", description="Período: today, week, month ou custom"),
    custom_date: Optional[date] = Query(None, description="Data específica para período custom"),
    start_date: Optional[date] = Query(None, description="Data inicial (sobrescreve period)"),
    end_date: Optional[date] = Query(None, description="Data final (sobrescreve period)"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Resumo de Vendas com Lucro**

    Retorna agregação completa de vendas: receita, custo, desconto, lucro e margem.
    Ideal para Dashboard e Página de Relatórios.

    **PERMISSÃO:** Admin, Gerente e Vendedor

    **Parâmetros:**
    - `period`: Período predefinido (today, week, month, custom)
    - `custom_date`: Data para período custom
    - `start_date`: Data inicial customizada (sobrescreve period)
    - `end_date`: Data final customizada (sobrescreve period)

    **Resposta:**
    - `total_revenue`: Receita bruta (soma dos itens vendidos)
    - `total_sales`: Número total de vendas
    - `total_discount`: Soma de todos os descontos
    - `average_ticket`: Ticket médio por venda
    - `total_cost`: Custo total dos produtos vendidos
    - `profit`: Lucro bruto (receita - custo)
    - `margin_percentage`: Margem de lucro em %
    - `sales`: Array de vendas para relatório

    **Exemplo:** GET /reports/sales-summary?period=month
    """
    today = date.today()

    # Definir datas usando período ou customizado
    if start_date and end_date:
        # Usar datas customizadas se informadas
        query_start = start_date
        query_end = end_date
    else:
        # Usar período predefinido
        query_start, query_end = get_date_range(period, custom_date)

    if not query_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido"
        )

    # Validar datas
    if query_start > query_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data inicial não pode ser maior que data final"
        )

    # Buscar todas as vendas COMPLETED no período
    sales = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.created_at >= datetime.combine(query_start, datetime.min.time()),
        Sale.created_at < datetime.combine(query_end + timedelta(days=1), datetime.min.time()),
        Sale.status == SaleStatus.COMPLETED
    ).all()

    # Calcular métricas
    total_revenue = 0.0
    total_discount = 0.0
    total_cost = 0.0
    sales_count = len(sales)
    sales_data = []
    products_without_cost = set()  # Produtos sem preço de custo

    for sale in sales:
        # Somar receita e desconto
        total_revenue += sale.total_amount
        total_discount += sale.discount_amount

        # Calcular custo total usando custo do produto
        for item in sale.items:
            # Buscar o custo atual do produto
            cost_price = item.product.cost_price if item.product.cost_price is not None else 0.0
            
            # Registrar produtos sem preço de custo
            if cost_price == 0.0 or item.product.cost_price is None:
                products_without_cost.add((item.product.id, item.product.name))
            
            total_cost += float(cost_price) * item.quantity

        # Adicionar venda ao array
        sales_data.append({
            "sale_id": sale.id,
            "customer_name": sale.customer.name if sale.customer else "N/A",
            "sale_date": sale.created_at.isoformat(),
            "total_amount": float(sale.total_amount)
        })

    profit = total_revenue - total_cost
    margin_percentage = (profit / total_revenue * 100) if total_revenue > 0 else 0.0
    average_ticket = (total_revenue / sales_count) if sales_count > 0 else 0.0
    
    # Preparar mensagem de aviso se houver produtos sem custo
    warning = None
    if products_without_cost:
        warning = {
            "message": "Não é possível calcular o lucro com precisão. Alguns produtos vendidos não possuem preço de custo cadastrado. Para obter relatórios de lucro precisos, é necessário cadastrar o preço de compra de todos os produtos.",
            "products_count": len(products_without_cost),
            "products": [
                {"id": prod_id, "name": prod_name}
                for prod_id, prod_name in sorted(products_without_cost, key=lambda x: x[1])
            ]
        }
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_sales": sales_count,
        "total_discount": round(total_discount, 2),
        "average_ticket": round(average_ticket, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "margin_percentage": round(margin_percentage, 2),
        "sales": sales_data,
        "warning": warning
    }
