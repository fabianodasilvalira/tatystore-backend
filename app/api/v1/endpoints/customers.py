"""
Endpoints de Clientes (v1)
CRUD com isolamento por empresa
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.customer import Customer
from app.models.installment import Installment, InstallmentStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from sqlalchemy import func, select
from app.schemas.pagination import paginate

router = APIRouter()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo cliente")
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Cadastrar Novo Cliente**
    
    Cria um novo cliente vinculado à empresa do usuário autenticado.
    
    **Requer:** Admin ou Gerente
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
    
    **Resposta:** Lista de clientes com metadados de paginação
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
        total_due = db.query(func.sum(Installment.amount)).filter(
            Installment.customer_id == customer.id,
            Installment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.OVERDUE])
        ).scalar() or 0.0
        
        result.append({
            **CustomerResponse.model_validate(customer).model_dump(),
            "total_debt": float(total_due)
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
    
    Retorna informações detalhadas do cliente incluindo dívidas pendentes.
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
    
    # Obter dívidas
    total_due = db.query(func.sum(Installment.amount)).filter(
        Installment.customer_id == customer.id,
        Installment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.OVERDUE])
    ).scalar() or 0.0
    
    return {
        **CustomerResponse.model_validate(customer).model_dump(),
        "total_debt": float(total_due)
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
    
    # Atualizar campos
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.utcnow()
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
    customer.updated_at = datetime.utcnow()
    db.commit()
    
    return None
