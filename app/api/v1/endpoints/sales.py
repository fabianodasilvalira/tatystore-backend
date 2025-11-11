"""
Endpoints de Vendas (v1)
Suporta cash, credit e PIX com gestão automática de estoque e parcelas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.sale import Sale, SaleItem, PaymentType, SaleStatus
from app.models.product import Product
from app.models.customer import Customer
from app.models.installment import Installment, InstallmentStatus
from app.schemas.sale import SaleCreate, SaleResponse
from app.schemas.pagination import paginate

router = APIRouter()


def get_date_range(period: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """
    Helper para obter range de datas baseado no período
    
    Args:
        period: 'today', 'week', 'month', 'custom'
        start_date: Data inicial para período customizado
        end_date: Data final para período customizado
    
    Returns:
        Tupla (start_date, end_date)
    """
    today = date.today()
    
    if period == "today":
        return today, today + timedelta(days=1)
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=7)
    elif period == "month":
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        return date(today.year, today.month, 1), next_month
    elif period == "custom":
        if not start_date or not end_date:
            return None, None
        return start_date, end_date + timedelta(days=1)  # Incluir dia final
    else:
        return None, None


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nova venda")
def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Registrar Nova Venda**
    
    Cria uma nova venda com:
    - Validação de estoque
    - Cálculo automático de totais
    - Geração de parcelas (se crediário)
    - Desconto aplicado
    
    **PERMISSÃO:** Gerente e Vendedor
    
    **Tipos de Pagamento:**
    - `cash`: À vista
    - `credit`: Crediário com parcelas
    - `pix`: PIX com QR code
    """
    # Validar cliente
    customer = db.query(Customer).filter(
        Customer.id == sale_data.customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Validar e processar itens
    subtotal = 0.0
    sale_items = []
    
    for item_data in sale_data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.company_id == current_user.company_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Produto {item_data.product_id} não encontrado"
            )
        
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para {product.name}. Disponível: {product.stock_quantity}"
            )
        
        item_total = item_data.unit_price * item_data.quantity
        subtotal += item_total
        
        sale_items.append({
            "product": product,
            "data": item_data,
            "total": item_total
        })
    
    # Validar desconto
    if sale_data.discount_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Desconto não pode ser negativo"
        )
    
    if sale_data.discount_amount > subtotal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Desconto não pode ser maior que o subtotal"
        )
    
    # Validar desconto em relação ao valor total
    discount_percentage = (sale_data.discount_amount / subtotal * 100) if subtotal > 0 else 0
    if discount_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Desconto não pode exceder 100% do valor"
        )
    
    # Validar quantidade de parcelas
    if sale_data.payment_type == PaymentType.CREDIT:
        if not sale_data.installments_count or sale_data.installments_count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crediário requer no mínimo 1 parcela"
            )
        if sale_data.installments_count > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo de 60 parcelas permitidas"
            )
    
    total_amount = subtotal - sale_data.discount_amount
    
    # Validar que total não fica negativo
    if total_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor total não pode ser negativo"
        )
    
    # Validar quantidade de itens
    if not sale_data.items or len(sale_data.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venda deve ter pelo menos 1 item"
        )
    
    # Criar venda
    sale = Sale(
        customer_id=customer.id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        payment_type=sale_data.payment_type,
        subtotal=subtotal,
        discount_amount=sale_data.discount_amount,
        total_amount=total_amount,
        installments_count=sale_data.installments_count,
        notes=sale_data.notes,
        status=SaleStatus.COMPLETED
    )
    
    db.add(sale)
    db.flush()
    
    # Criar itens e debitar estoque
    for item_info in sale_items:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=item_info["product"].id,
            quantity=item_info["data"].quantity,
            unit_price=item_info["data"].unit_price,
            total_price=item_info["total"]
        )
        db.add(sale_item)
        
        # Debitar estoque
        item_info["product"].stock_quantity -= item_info["data"].quantity
    
    # Gerar parcelas para crediário
    if sale_data.payment_type == PaymentType.CREDIT:
        num_installments = sale_data.installments_count or 1
        if num_installments < 1:
            num_installments = 1
        
        # Calcular valor de cada parcela
        base_amount = total_amount / num_installments
        
        for i in range(num_installments):
            # Ajustar última parcela para compensar arredondamentos
            if i == num_installments - 1:
                amount = total_amount - (base_amount * (num_installments - 1))
            else:
                amount = base_amount
            
            due_date = date.today() + timedelta(days=30 * (i + 1))
            
            installment = Installment(
                sale_id=sale.id,
                customer_id=customer.id,
                company_id=current_user.company_id,
                installment_number=i + 1,
                amount=amount,
                due_date=due_date,
                status=InstallmentStatus.PENDING
            )
            db.add(installment)
    
    db.commit()
    db.refresh(sale)
    
    return sale


# FastAPI processa rotas na ordem de definição, então rotas com paths dinâmicos devem vir por último

# Ordem correta: /by-customer/{}/products -> /by-customer/{} -> /products/top-sellers -> / -> /{id}

@router.get("/by-customer/{customer_id}/products", response_model=List[dict], summary="Produtos que cliente comprou")
def get_customer_purchased_products(
    customer_id: int,
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(50, ge=1, le=200, description="Quantidade de registros (máximo 200)"),
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Produtos que Cliente Já Comprou**
    
    Lista todos os produtos distintos que um cliente específico já comprou, ordenados 
    por frequência de compra (produtos mais comprados primeiro).
    
    **PERMISSÃO:** Gerente e Vendedor (dados da própria empresa)
    
    **Utilidade:** Útil para sugestões de venda e análise de preferências.
    
    **Retorna:** 
    - `product_id`: ID do produto
    - `product_name`: Nome do produto
    - `brand`: Marca do produto
    - `times_purchased`: Quantas vezes foi comprado
    - `total_quantity`: Quantidade total comprada
    - `last_purchase_date`: Data da última compra
    - `total_spent`: Total gasto neste produto
    
    **Exemplo:** GET /sales/by-customer/123/products?skip=0&limit=50
    """
    # Verificar se cliente existe e pertence à empresa
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Query para obter produtos comprados pelo cliente com estatísticas
    from sqlalchemy import func, desc
    
    products_purchased = db.query(
        SaleItem.product_id,
        Product.name.label("product_name"),
        Product.brand,
        func.count(SaleItem.id).label("times_purchased"),
        func.sum(SaleItem.quantity).label("total_quantity"),
        func.max(Sale.created_at).label("last_purchase_date"),
        func.sum(SaleItem.total_price).label("total_spent")
    ).join(Sale, SaleItem.sale_id == Sale.id)\
     .join(Product, SaleItem.product_id == Product.id)\
     .filter(
        Sale.customer_id == customer_id,
        Sale.company_id == current_user.company_id,
        Sale.status == SaleStatus.COMPLETED
     ).group_by(SaleItem.product_id, Product.name, Product.brand)\
     .order_by(desc("times_purchased"))\
     .offset(skip)\
     .limit(limit)\
     .all()
    
    return [
        {
            "product_id": item[0],
            "product_name": item[1],
            "brand": item[2],
            "times_purchased": item[3],
            "total_quantity": item[4],
            "last_purchase_date": item[5],
            "total_spent": float(item[6]) if item[6] else 0.0
        }
        for item in products_purchased
    ]


@router.get("/by-customer/{customer_id}", response_model=dict, summary="Histórico completo de vendas por cliente")
def get_customer_sales_history(
    customer_id: int,
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade de registros (máximo 100)"),
    sort: str = Query("date_desc", regex="^(date_desc|date_asc|amount_desc|amount_asc)$"),
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Histórico Detalhado de Vendas por Cliente**
    
    Retorna todas as vendas de um cliente com estatísticas consolidadas e análise completa.
    
    **PERMISSÃO:** Gerente e Vendedor (dados da própria empresa)
    
    **Parâmetros:**
    - `sort`: Ordenação dos resultados
      - `date_desc`: Data mais recente primeiro (padrão)
      - `date_asc`: Data mais antiga primeiro
      - `amount_desc`: Maior valor primeiro
      - `amount_asc`: Menor valor primeiro
    
    **Retorna Objeto com:**
    - `customer`: Dados básicos do cliente
    - `statistics`: Estatísticas consolidadas (total gasto, ticket médio, etc)
    - `sales`: Lista paginada de vendas detalhadas
    - `metadata`: Informações de paginação
    
    **Exemplo:** GET /sales/by-customer/123?sort=date_desc&limit=20
    """
    # Verificar se cliente existe e pertence à empresa
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Query base
    base_query = db.query(Sale).filter(
        Sale.customer_id == customer_id,
        Sale.company_id == current_user.company_id
    )
    
    # Ordenação
    from sqlalchemy import desc, asc
    sort_mapping = {
        "date_desc": desc(Sale.created_at),
        "date_asc": asc(Sale.created_at),
        "amount_desc": desc(Sale.total_amount),
        "amount_asc": asc(Sale.total_amount),
    }
    query = base_query.order_by(sort_mapping[sort])
    
    # Contar total
    total_sales = query.count()
    
    # Paginação
    sales = query.offset(skip).limit(limit).all()
    
    # Calcular estatísticas
    completed_sales = base_query.filter(Sale.status == SaleStatus.COMPLETED).all()
    
    total_spent = sum(sale.total_amount for sale in completed_sales)
    completed_count = len(completed_sales)
    
    stats = {
        "total_sales": total_sales,
        "completed_sales": completed_count,
        "total_spent": float(total_spent),
        "average_ticket": float(total_spent / completed_count) if completed_count > 0 else 0.0,
        "total_items_purchased": sum(
            sum(item.quantity for item in sale.items) 
            for sale in completed_sales
        ),
        "first_purchase_date": min(
            (sale.created_at for sale in completed_sales), 
            default=None
        ),
        "last_purchase_date": max(
            (sale.created_at for sale in completed_sales), 
            default=None
        ) if completed_sales else None,
        "most_used_payment": max(
            set((sale.payment_type for sale in completed_sales)),
            key=lambda x: sum(1 for s in completed_sales if s.payment_type == x),
            default=None
        ) if completed_sales else None
    }
    
    # Converter vendas para dicionário
    sales_data = [SaleResponse.model_validate(sale).model_dump() for sale in sales]
    
    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "cpf": customer.cpf
        },
        "statistics": stats,
        "sales": sales_data,
        "metadata": {
            "total": total_sales,
            "page": skip // limit + 1 if limit > 0 else 1,
            "limit": limit,
            "skip": skip,
            "has_next": (skip + limit) < total_sales,
            "has_prev": skip > 0
        }
    }


@router.get("/products/top-sellers", response_model=list, summary="Produtos mais vendidos")
def get_top_selling_products(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente (opcional)"),
    metric: str = Query("quantity", regex="^(quantity|revenue)$"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade de produtos (máximo 100)"),
    period: Optional[str] = Query("month", description="Período: today, week, month, custom"),
    start_date: Optional[date] = Query(None, description="Data inicial (para period=custom)"),
    end_date: Optional[date] = Query(None, description="Data final (para period=custom)"),
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Produtos Mais Vendidos (Top Sellers)**
    
    Ranking de produtos mais vendidos por quantidade ou faturamento em um período.
    
    **PERMISSÃO:** Gerente e Vendedor
    
    **Parâmetros:**
    - `customer_id` (Opcional): Se fornecido, retorna produtos mais comprados por esse cliente. Se omitido, retorna mais vendidos da loja em geral.
    - `metric`: Critério de ranking
      - `quantity`: Quantidade de unidades vendidas (padrão)
      - `revenue`: Faturamento total
    - `period`: Período de análise (padrão: month)
      - `today`: Vendas de hoje
      - `week`: Vendas da semana atual
      - `month`: Vendas do mês atual
      - `custom`: Intervalo personalizado
    - `limit`: Quantidade de produtos a retornar (máximo 100)
    
    **Retorna Array de Objetos com:**
    - `product_id`: ID do produto
    - `name`: Nome do produto
    - `purchase_count`: Quantas vezes esteve em uma compra
    - `quantity_sold`: Quantidade total de unidades vendidas
    - `revenue`: Receita total gerada
    
    **Exemplo:** GET /sales/products/top-sellers?metric=revenue&period=month&limit=20
    **Exemplo com Cliente:** GET /sales/products/top-sellers?customer_id=123&limit=10
    """
    # Determinar período
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    if not date_start or not date_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para period=custom, informe start_date e end_date no formato YYYY-MM-DD"
        )
    
    from sqlalchemy import func, desc
    
    # Query para top sellers
    query = db.query(
        Product.id,
        Product.name,
        func.count(Sale.id).label("purchase_count"),
        func.sum(SaleItem.quantity).label("quantity_sold"),
        func.sum(SaleItem.total_price).label("revenue")
    ).join(SaleItem, Product.id == SaleItem.product_id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(
        Product.company_id == current_user.company_id,
        Sale.company_id == current_user.company_id,
        Sale.status == SaleStatus.COMPLETED,
        Sale.created_at >= datetime.combine(date_start, datetime.min.time()),
        Sale.created_at < datetime.combine(date_end, datetime.min.time())
     )
    
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
    
    query = query.group_by(Product.id, Product.name)
    
    # Ordenar por métrica
    if metric == "revenue":
        query = query.order_by(desc("revenue"))
    else:  # quantity
        query = query.order_by(desc("quantity_sold"))
    
    top_products = query.limit(limit).all()
    
    return [
        {
            "product_id": item[0],
            "name": item[1],
            "purchase_count": item[2],
            "quantity_sold": item[3],
            "revenue": float(item[4]) if item[4] else 0.0
        }
        for item in top_products
    ]


@router.get("/", response_model=dict, summary="Listar vendas da empresa")
def list_sales(
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade de registros (máximo 100)"),
    search: Optional[str] = Query(None, description="Buscar por nome do cliente, CPF, email ou telefone"),
    customer_id: Optional[int] = Query(None, description="Filtrar por ID do cliente"),
    status: Optional[str] = Query(None, description="Filtrar por status (completed, cancelled)"),
    payment_type: Optional[str] = Query(None, description="Filtrar por tipo de pagamento (cash, credit, pix)"),
    period: Optional[str] = Query(None, description="Período: today, week, month, custom"),
    start_date: Optional[date] = Query(None, description="Data inicial (para period=custom)"),
    end_date: Optional[date] = Query(None, description="Data final (para period=custom)"),
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Listar Vendas da Empresa**
    
    Lista todas as vendas com filtros opcionais e paginação.
    
    **PERMISSÃO:** Gerente e Vendedor (dados da própria empresa)
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Filtros Básicos:**
    - `search`: Buscar por nome, CPF, email ou telefone do cliente (busca parcial)
    - `customer_id`: Filtrar por ID do cliente exato
    - `status`: Filtrar por status (completed, cancelled)
    - `payment_type`: Filtrar por tipo de pagamento (cash, credit, pix)
    
    **Filtros de Data:**
    - `period`: Período predefinido
      - `today`: Vendas de hoje
      - `week`: Vendas da semana atual (Segunda a Domingo)
      - `month`: Vendas do mês atual
      - `custom`: Intervalo personalizado (requer start_date e end_date)
    - `start_date`: Data inicial para filtro customizado (formato: YYYY-MM-DD)
    - `end_date`: Data final para filtro customizado (formato: YYYY-MM-DD)
    
    **Resposta:** 
    - `total`: Total de registros
    - `data`: Lista de vendas com cliente, itens e parcelas
    
    **Exemplos de Uso:**
    - Vendas de hoje: `?period=today`
    - Vendas da semana: `?period=week`
    - Vendas do mês: `?period=month`
    - Intervalo personalizado: `?period=custom&start_date=2025-01-01&end_date=2025-01-31`
    - Buscar por cliente: `?search=silva`
    - Combinar filtros: `?period=month&payment_type=cash&search=silva&limit=20`
    """
    query = db.query(Sale).join(Customer, Sale.customer_id == Customer.id).filter(
        Sale.company_id == current_user.company_id
    )
    
    if search:
        search_term = f"%{search}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.cpf.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )
    
    # Aplicar filtro de cliente por ID
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
    
    if status:
        # Normalizar: canceled -> cancelled, uppercase
        normalized_status = status.lower()
        if normalized_status == "canceled":
            normalized_status = "cancelled"
        
        # Converter para uppercase para corresponder ao enum
        normalized_status = normalized_status.upper()
        
        # Validar se é um status válido
        try:
            status_enum = SaleStatus[normalized_status]
            query = query.filter(Sale.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status inválido: '{status}'. Use: completed, cancelled, pending"
            )
    
    if payment_type:
        # Converter para uppercase para corresponder ao enum
        normalized_payment = payment_type.upper()
        
        # Validar se é um tipo de pagamento válido
        try:
            payment_enum = PaymentType[normalized_payment]
            query = query.filter(Sale.payment_type == payment_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de pagamento inválido: '{payment_type}'. Use: cash, credit, pix"
            )
    
    # Aplicar filtros de data
    if period:
        date_start, date_end = get_date_range(period, start_date, end_date)
        
        if not date_start or not date_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para period=custom, informe start_date e end_date no formato YYYY-MM-DD"
            )
        
        query = query.filter(
            Sale.created_at >= datetime.combine(date_start, datetime.min.time()),
            Sale.created_at < datetime.combine(date_end, datetime.min.time())
        )
    
    # Contar total antes da paginação
    total = query.count()
    
    # Ordenar por data mais recente
    query = query.order_by(Sale.created_at.desc())
    
    # Aplicar paginação
    sales = query.offset(skip).limit(limit).all()
    
    sales_data = [SaleResponse.model_validate(sale).model_dump() for sale in sales]
    
    return {
        "total": total,
        "data": sales_data
    }


@router.get("/{sale_id}", response_model=SaleResponse, summary="Obter dados da venda")
def get_sale(
    sale_id: int,
    current_user: User = Depends(require_role("gerente", "Gerente", "vendedor", "Vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados de uma Venda**
    
    Retorna informações detalhadas de uma venda incluindo itens e parcelas.
    
    **PERMISSÃO:** Gerente e Vendedor (da própria empresa)
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada"
        )
    
    # Verificar isolamento
    if sale.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    return sale


@router.post("/{sale_id}/cancel", summary="Cancelar venda")
def cancel_sale(
    sale_id: int,
    current_user: User = Depends(require_role("gerente", "Gerente")),
    db: Session = Depends(get_db)
):
    """
    **Cancelar Venda**
    
    Cancela uma venda, restaurando estoque e cancelando parcelas.
    
    **PERMISSÃO:** Apenas Gerente
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada"
        )
    
    # Verificar isolamento
    if sale.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    if sale.status == SaleStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venda já foi cancelada"
        )
    
    product_updates = {}
    for item in sale.items:
        if item.product_id not in product_updates:
            product_updates[item.product_id] = 0
        product_updates[item.product_id] += item.quantity
    
    # Apply stock restoration in single transaction
    for product_id, quantity_to_restore in product_updates.items():
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.stock_quantity += quantity_to_restore
    
    # Cancelar parcelas não pagas
    for installment in sale.installments:
        if installment.status != InstallmentStatus.PAID:
            installment.status = InstallmentStatus.CANCELLED
    
    sale.status = SaleStatus.CANCELLED
    db.commit()
    
    return {"id": sale.id, "message": "Venda cancelada com sucesso"}
