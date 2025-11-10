"""
Endpoints de Vendas (v1)
Suporta cash, credit e PIX com gestão automática de estoque e parcelas
"""
from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED, summary="Registrar nova venda")
def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Registrar Nova Venda**
    
    Cria uma nova venda com:
    - Validação de estoque
    - Cálculo automático de totais
    - Geração de parcelas (se crediário)
    - Desconto aplicado
    
    **Requer:** Admin ou Gerente
    
    **Tipos de Pagamento:**
    - `cash`: À vista
    - `credit`: Crediário com parcelas
    - `pix`: PIX com QR code
    """
    # Validar cliente
    customer = db.query(Customer).filter(
        Customer.id == sale_data.customer_id,
        Customer.company_id == current_user.company_id,
        Customer.is_active == True
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado ou inativo"
        )
    
    # Validar e processar itens
    subtotal = 0.0
    sale_items = []
    
    for item_data in sale_data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.company_id == current_user.company_id,
            Product.is_active == True
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


@router.get("/", response_model=List[dict], summary="Listar vendas da empresa")
def list_sales(
    skip: int = 0,
    limit: int = 10,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    payment_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Vendas da Empresa**
    
    Lista todas as vendas com filtros opcionais.
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Filtros:**
    - `customer_id`: Filtrar por cliente
    - `status`: Filtrar por status
    - `payment_type`: Filtrar por tipo de pagamento
    
    **Resposta:** Lista de vendas
    """
    query = db.query(Sale).filter(Sale.company_id == current_user.company_id)
    
    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)
    
    if status:
        query = query.filter(Sale.status == status)
    
    if payment_type:
        query = query.filter(Sale.payment_type == payment_type)
    
    query = query.order_by(Sale.created_at.desc())
    
    sales = query.offset(skip).limit(limit).all()
    
    sales_data = [SaleResponse.model_validate(sale).model_dump() for sale in sales]
    
    return sales_data


@router.get("/{sale_id}", response_model=SaleResponse, summary="Obter dados da venda")
def get_sale(
    sale_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados de uma Venda**
    
    Retorna informações detalhadas de uma venda incluindo itens e parcelas.
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
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Cancelar Venda**
    
    Cancela uma venda, restaurando estoque e cancelando parcelas.
    
    **Requer:** Admin ou Gerente
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
