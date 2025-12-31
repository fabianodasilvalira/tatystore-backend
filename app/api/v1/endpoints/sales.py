"""
Endpoints de Vendas (v1)
Suporta cash, credit e PIX com gestão automática de estoque e parcelas
"""
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.sale import Sale, PaymentType, SaleStatus, SaleItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.installment import Installment, InstallmentStatus
from app.models.stock_movement import StockMovement, MovementType
from app.schemas.sale import SaleCreate, SaleResponse
from app.schemas.pagination import paginate
from app.api.v1.endpoints.installments import _calculate_installment_balance, _enrich_installment_with_balance

router = APIRouter()


def get_date_range(period: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Helper para obter range de datas baseado no período"""
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
        return start_date, end_date + timedelta(days=1)
    else:
        return None, None


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nova venda")
def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Registrar Nova Venda com validação completa"""
    
    # DEBUG
    try:
        print(f"DEBUG SALES: sale_data type: {type(sale_data)}")
        print(f"DEBUG SALES: sale_data keys: {sale_data.model_dump().keys() if hasattr(sale_data, 'model_dump') else sale_data.__dict__.keys()}")
        print(f"DEBUG SALES: has first_due_date? {hasattr(sale_data, 'first_due_date')}")
        if hasattr(sale_data, 'first_due_date'):
            print(f"DEBUG SALES: first_due_date value: {sale_data.first_due_date}")
    except Exception as e:
        print(f"DEBUG SALES EXCEPTION: {e}")

    try:
        # Validar cliente com lock
        customer = db.query(Customer).filter(
            Customer.id == sale_data.customer_id,
            Customer.company_id == current_user.company_id
        ).with_for_update().first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        
        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente está inativo e não pode realizar compras"
            )
        
        # Validar dados completos do cliente para vendas a crediário
        if sale_data.payment_type == "credit":
            missing_fields = []
            if not customer.cpf:
                missing_fields.append("CPF")
            if not customer.phone:
                missing_fields.append("Telefone")
            if not customer.address:
                missing_fields.append("Endereço")
            
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Para vendas a crediário, o cliente precisa ter: {', '.join(missing_fields)}"
                )
        
        # Validar e processar itens
        subtotal = 0.0
        sale_items = []
        
        if not sale_data.items or len(sale_data.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Venda deve ter pelo menos 1 item"
            )
        
        for item_data in sale_data.items:
            # Validar quantidade
            if item_data.quantity <= 0 or item_data.quantity > 10000:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Quantidade deve estar entre 1 e 10.000 unidades"
                )
            
            # CORREÇÃO #4: Validar preço de venda
            if item_data.unit_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Preço de venda deve ser maior que zero"
                )
            
            product = db.query(Product).filter(
                Product.id == item_data.product_id,
                Product.company_id == current_user.company_id
            ).with_for_update().first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Produto {item_data.product_id} não encontrado"
                )
            
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Produto {product.name} está inativo e não pode ser vendido"
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
        
        # Validar quantidade de parcelas
        if sale_data.payment_type == PaymentType.CREDIT:
            if not sale_data.installments_count or sale_data.installments_count < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Crediário requer no mínimo 1 parcela"
                )
            if sale_data.installments_count > 60:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Máximo de 60 parcelas permitidas"
                )
        
        total_amount = subtotal - sale_data.discount_amount
        
        # CORREÇÃO #3: Validar que total não fica negativo OU ZERO
        if total_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valor total deve ser maior que zero"
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
        
        for item_info in sale_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item_info["product"].id,
                quantity=item_info["data"].quantity,
                unit_price=item_info["data"].unit_price,
                total_price=item_info["total"],
                unit_cost_price=item_info["product"].cost_price or 0.0  # Salva o custo historico
            )
            db.add(sale_item)
            
            # Debitar estoque
            previous_stock = item_info["product"].stock_quantity
            item_info["product"].stock_quantity -= item_info["data"].quantity
            new_stock = item_info["product"].stock_quantity
            
            # Registrar movimento de estoque para auditoria
            stock_movement = StockMovement(
                product_id=item_info["product"].id,
                user_id=current_user.id,
                company_id=current_user.company_id,
                movement_type=MovementType.SALE,
                quantity=-item_info["data"].quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                reference_type="sale",
                reference_id=sale.id,
                notes=f"Venda #{sale.id} - {item_info['data'].quantity} unidades"
            )
            db.add(stock_movement)
        
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
                
                # MELHORIA #8: Data de vencimento personalizada
                if sale_data.first_due_date:
                    # Se for a primeira parcela (i=0), usa a data exata
                    # Se for as seguintes, soma 30 dias * i a partir da primeira data
                    if i == 0:
                        due_date = sale_data.first_due_date
                    else:
                        due_date = sale_data.first_due_date + timedelta(days=30 * i)
                else:
                    # Comportamento padrão: 30 dias a partir de hoje
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
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar venda: {str(e)}"
        )


@router.get("/products/top-sellers", summary="Produtos mais vendidos")
def get_top_selling_products(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente (opcional)"),
    metric: str = Query("quantity", pattern="^(quantity|revenue)$"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade de produtos (máximo 100)"),
    period: Optional[str] = Query("month", description="Período: today, week, month, custom"),
    start_date: Optional[date] = Query(None, description="Data inicial (para period=custom)"),
    end_date: Optional[date] = Query(None, description="Data final (para period=custom)"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Produtos Mais Vendidos (Top Sellers)"""
    try:
        # Determinar período
        date_start, date_end = get_date_range(period, start_date, end_date)
        
        if not date_start or not date_end:
            return []
        
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
                "id": item.id,
                "name": item.name,
                "value": item.quantity_sold if metric == "quantity" else item.revenue,
                "quantity": item.quantity_sold,
                "revenue": item.revenue
            }
            for item in top_products
        ]
    except Exception as e:
        print(f"Erro ao buscar top sellers: {e}")
        return []
    
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


@router.get("/", summary="Listar vendas da empresa")
def list_sales(
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Quantidade de registros (opcional, máximo 100)"),
    search: Optional[str] = Query(None, description="Buscar por nome do cliente, CPF, email ou telefone"),
    customer_id: Optional[int] = Query(None, description="Filtrar por ID do cliente"),
    status: Optional[str] = Query(None, description="Filtrar por status (completed, cancelled)"),
    payment_type: Optional[str] = Query(None, description="Filtrar por tipo de pagamento (cash, credit, pix)"),
    period: Optional[str] = Query(None, description="Período: today, week, month, custom"),
    start_date: Optional[date] = Query(None, description="Data inicial (para period=custom)"),
    end_date: Optional[date] = Query(None, description="Data final (para period=custom)"),
    show_inactive_customers: bool = Query(False, description="Incluir vendas de clientes inativos"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Listar Vendas da Empresa com filtros opcionais e paginação"""
    query = db.query(Sale).join(Customer, Sale.customer_id == Customer.id).filter(
        Sale.company_id == current_user.company_id
    )
    
    # MELHORIA #11: Filtrar clientes inativos por padrão
    if not show_inactive_customers and not customer_id:
        query = query.filter(Customer.is_active == True)
    
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
    query = query.offset(skip)
    
    if limit is None:
        sales = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 100:
            limit = 100
        sales = query.limit(limit).all()
    
    sales_data = []
    for sale in sales:
        sale_dict = SaleResponse.model_validate(sale).model_dump()
        enriched_installments = []
        for installment in sale.installments:
            enriched_inst = _enrich_installment_with_balance(installment)
            enriched_installments.append(enriched_inst)
        sale_dict["installments"] = enriched_installments
        sales_data.append(sale_dict)
    
    return paginate(sales_data, total, skip, limit)


@router.get("/by-customer/{customer_id}/products", summary="Produtos que cliente comprou")
def get_customer_purchased_products(
    customer_id: int,
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Quantidade de registros (opcional, máximo 200)"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Produtos que Cliente Já Comprou"""
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
    
    query = db.query(
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
     .order_by(desc("times_purchased"))
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        products_purchased = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 200:
            limit = 200
        products_purchased = query.limit(limit).all()
    
    result_data = [
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
    
    return paginate(result_data, total, skip, limit)


@router.get("/by-customer/{customer_id}", summary="Histórico completo de vendas por cliente")
def get_customer_sales_history(
    customer_id: int,
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Quantidade de registros (opcional, máximo 100)"),
    sort: str = Query("date_desc", pattern="^(date_desc|date_asc|amount_desc|amount_asc)$"),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Histórico Detalhado de Vendas por Cliente"""
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
    query = query.offset(skip)
    
    if limit is not None:
        if limit > 100:
            limit = 100
        query = query.limit(limit)
    
    sales = query.all()
    
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
            "page": (skip // limit) + 1 if limit and limit > 0 else 1,
            "limit": limit if limit else total_sales,
            "skip": skip,
            "has_next": (skip + (limit if limit else total_sales)) < total_sales,
            "has_prev": skip > 0
        }
    }


@router.get("/{sale_id}", response_model=SaleResponse, summary="Obter dados da venda")
def get_sale(
    sale_id: int,
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """Obter Dados de uma Venda"""
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

    sale_data = SaleResponse.model_validate(sale).model_dump()
    sale_data["profit"] = float(sale.profit)
    sale_data["profit_margin_percentage"] = float(sale.profit_margin_percentage)
    
    enriched_installments = []
    for installment in sale.installments:
        enriched_inst = _enrich_installment_with_balance(installment)
        enriched_installments.append(enriched_inst)
    sale_data["installments"] = enriched_installments

    return sale_data


@router.post("/{sale_id}/cancel", summary="Cancelar venda")
def cancel_sale(
    sale_id: int,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """Cancelar Venda"""
    
    sale = db.query(Sale).filter(Sale.id == sale_id).with_for_update().first()
    
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
    
    # CORREÇÃO #2: Verificar se há parcelas pagas
    paid_installments = [i for i in sale.installments if i.status == InstallmentStatus.PAID]
    if paid_installments:
        total_paid = sum(i.amount for i in paid_installments)
        paid_count = len(paid_installments)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível cancelar venda com {paid_count} parcela(s) já paga(s) (R$ {total_paid:.2f} recebidos). Realize estorno manual antes de cancelar."
        )
    
    product_updates = {}
    for item in sale.items:
        if item.product_id not in product_updates:
            product_updates[item.product_id] = 0
        product_updates[item.product_id] += item.quantity
    
    # Apply stock restoration in single transaction with lock
    for product_id, quantity_to_restore in product_updates.items():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if product:
            previous_stock = product.stock_quantity
            product.stock_quantity += quantity_to_restore
            new_stock = product.stock_quantity
            
            # MELHORIA #6: Registrar movimento de estoque para auditoria
            stock_movement = StockMovement(
                product_id=product_id,
                user_id=current_user.id,
                company_id=current_user.company_id,
                movement_type=MovementType.CANCEL,
                quantity=quantity_to_restore,
                previous_stock=previous_stock,
                new_stock=new_stock,
                reference_type="sale_cancel",
                reference_id=sale_id,
                notes=f"Cancelamento da venda #{sale_id} - {quantity_to_restore} unidades restauradas"
            )
            db.add(stock_movement)
    
    # Cancelar parcelas não pagas
    for installment in sale.installments:
        if installment.status != InstallmentStatus.PAID:
            installment.status = InstallmentStatus.CANCELLED
    
    sale.status = SaleStatus.CANCELLED
    db.commit()
    
    return {"id": sale.id, "message": "Venda cancelada com sucesso"}
