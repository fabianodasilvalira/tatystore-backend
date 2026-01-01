"""
Endpoints de Clientes (v1)
CRUD com isolamento por empresa
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date as date_type

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.customer import Customer
from app.models.installment import Installment, InstallmentStatus
from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from sqlalchemy import func, select
from app.schemas.pagination import paginate
from app.api.v1.endpoints.installments import _calculate_installment_balance
from app.core.datetime_utils import get_now_fortaleza_naive

router = APIRouter()


def _calculate_customer_debt(db: Session, customer_id: int) -> tuple[float, float]:
    """
    Calcula débito total e vencido do cliente considerando pagamentos parciais.
    Retorna: (total_debt, total_due)
    - total_debt: soma de saldos de TODAS parcelas não pagas
    - total_due: soma de saldos de parcelas VENCIDAS
    """
    # Todas as parcelas pendentes ou vencidas
    pending_overdue_installments = db.query(Installment).filter(
        Installment.customer_id == customer_id,
        Installment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.OVERDUE])
    ).all()
    
    total_debt = 0.0
    total_due = 0.0
    today = date_type.today()
    
    for installment in pending_overdue_installments:
        _, remaining = _calculate_installment_balance(installment)
        
        total_debt += remaining
        
        if installment.status == InstallmentStatus.OVERDUE or installment.due_date < today:
            total_due += remaining
    
    return total_debt, total_due


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo cliente")
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente", "vendedor"))
):
    """
    **Cadastrar Novo Cliente**
    
    Cria um novo cliente vinculado à empresa do usuário autenticado.
    
    **Requer:** Admin, Gerente ou Vendedor
    """
    # Verificar se email ou CPF já existem na empresa
    if customer_data.email:
        existing_email = db.query(Customer).filter(
            Customer.email == customer_data.email,
            Customer.company_id == current_user.company_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado nesta empresa"
            )
    
    if customer_data.cpf:
        existing_cpf = db.query(Customer).filter(
            Customer.cpf == customer_data.cpf,
            Customer.company_id == current_user.company_id
        ).first()
        if existing_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado nesta empresa"
            )
    
    # Criar cliente
    customer = Customer(
        **customer_data.model_dump(),
        company_id=current_user.company_id,
        is_active=True
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


@router.get("/", summary="Listar clientes da empresa")
async def list_customers(
    skip: int = 0,
    limit: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Listar Clientes da Empresa**
    
    Lista todos os clientes da empresa com resumo de dívidas.
    
    **Parâmetros:**
    - `search`: Buscar por nome ou CPF
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    
    **Resposta:** Lista de clientes paginada
    """
    query = db.query(Customer).filter(
        Customer.company_id == current_user.company_id
    )
    
    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) |
            (Customer.cpf.ilike(f"%{search}%"))
        )
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        customers = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 100:
            limit = 100
        customers = query.limit(limit).all()
    
    result = []
    for customer in customers:
        total_debt, total_due = _calculate_customer_debt(db, customer.id)
        
        result.append({
            **CustomerResponse.model_validate(customer).model_dump(),
            "total_debt": float(total_debt),
            "total_due": float(total_due)
        })
    
    return paginate(result, total, skip, limit)


@router.get("/{customer_id}", response_model=dict, summary="Obter dados do cliente")
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Obter Dados de um Cliente**
    
    Retorna informações detalhadas do cliente incluindo dívidas pendentes e vencidas.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Verificar isolamento
    if customer.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    total_debt, total_due = _calculate_customer_debt(db, customer.id)
    
    return {
        **CustomerResponse.model_validate(customer).model_dump(),
        "total_debt": float(total_debt),
        "total_due": float(total_due)
    }


@router.put("/{customer_id}", response_model=CustomerResponse, summary="Atualizar cliente")
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Atualizar Cliente**
    
    Atualiza informações de um cliente.
    
    **Requer:** Admin ou Gerente
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Verificar isolamento
    if customer.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    # Verificar se email ou CPF já existem em OUTRO cliente da empresa
    update_data = customer_data.model_dump(exclude_unset=True)
    
    if 'email' in update_data and update_data['email']:
        existing_email = db.query(Customer).filter(
            Customer.email == update_data['email'],
            Customer.company_id == current_user.company_id,
            Customer.id != customer_id  # Excluir o próprio cliente
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado para outro cliente nesta empresa"
            )
    
    if 'cpf' in update_data and update_data['cpf']:
        existing_cpf = db.query(Customer).filter(
            Customer.cpf == update_data['cpf'],
            Customer.company_id == current_user.company_id,
            Customer.id != customer_id  # Excluir o próprio cliente
        ).first()
        if existing_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado para outro cliente nesta empresa"
            )
    
    # Atualizar campos
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = get_now_fortaleza_naive()
    db.commit()
    db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar cliente")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Desativar Cliente**
    
    Desativa um cliente (soft delete).
    
    **Requer:** Admin ou Gerente
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    # Verificar isolamento
    if customer.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    customer.is_active = False
    customer.updated_at = get_now_fortaleza_naive()
    db.commit()
    
    return None
