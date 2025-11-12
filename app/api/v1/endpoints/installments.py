"""
Endpoints de Parcelas (v1)
Gerenciamento de crediário com atualização de status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.installment import Installment, InstallmentStatus
from app.schemas.installment import InstallmentResponse
from app.schemas.pagination import paginate

router = APIRouter()

@router.get("/overdue", summary="Listar parcelas vencidas")
def list_overdue_installments(
    skip: int = 0,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar Parcelas Vencidas
    
    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    """
    today = date.today()

    query = (
        db.query(Installment)
        .filter(
            Installment.company_id == current_user.company_id,
            Installment.status == InstallmentStatus.OVERDUE,
            Installment.due_date < today,
        )
        .order_by(Installment.due_date.asc())
    )
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        installments = query.all()
        limit = total if total > 0 else 1
    else:
        installments = query.limit(limit).all()
    
    installments_data = [InstallmentResponse.model_validate(i).model_dump() for i in installments]
    
    return paginate(installments_data, total, skip, limit)


@router.get("/", summary="Listar parcelas da empresa")
def list_installments(
    skip: int = 0,
    limit: Optional[int] = None,
    customer_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar Parcelas da Empresa com filtros
    
    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    - `customer_id`: Filtrar por cliente (opcional)
    - `status_filter`: Filtrar por status (opcional)
    """
    query = db.query(Installment).filter(
        Installment.company_id == current_user.company_id
    )

    if customer_id:
        query = query.filter(Installment.customer_id == customer_id)

    if status_filter:
        try:
            status_enum = InstallmentStatus(status_filter.lower())
            query = query.filter(Installment.status == status_enum)
        except ValueError:
            raise HTTPException(400, detail="Status inválido. Use: pending, paid, overdue, cancelled.")

    query = query.order_by(Installment.due_date.asc())
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        installments = query.all()
        limit = total if total > 0 else 1
    else:
        installments = query.limit(limit).all()

    installments_data = [InstallmentResponse.model_validate(i).model_dump() for i in installments]
    
    return paginate(installments_data, total, skip, limit)


@router.get("/{installment_id}", response_model=InstallmentResponse, summary="Obter dados da parcela")
def get_installment(
    installment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obter detalhes de uma parcela
    """
    installment = db.query(Installment).filter(Installment.id == installment_id).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")

    if installment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    return installment


@router.patch("/{installment_id}/pay", response_model=InstallmentResponse, summary="Marcar parcela como paga")
def pay_installment(
    installment_id: int,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    Marcar parcela como paga (Admin ou Gerente)
    """
    installment = db.query(Installment).filter(Installment.id == installment_id).first()

    if not installment:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")

    if installment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    if installment.status == InstallmentStatus.PAID:
        raise HTTPException(status_code=400, detail="Parcela já está paga")

    if installment.status == InstallmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Parcela está cancelada")

    installment.status = InstallmentStatus.PAID
    installment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(installment)

    return installment


@router.get("/customer/{customer_id}", summary="Listar parcelas do cliente")
def list_installments_by_customer(
    customer_id: int,
    skip: int = 0,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar Parcelas por Cliente
    
    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    """
    query = (
        db.query(Installment)
        .filter(
            Installment.company_id == current_user.company_id,
            Installment.customer_id == customer_id
        )
        .order_by(Installment.due_date.asc())
    )
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        installments = query.all()
        limit = total if total > 0 else 1
    else:
        installments = query.limit(limit).all()

    installments_data = [InstallmentResponse.model_validate(i).model_dump() for i in installments]
    
    return paginate(installments_data, total, skip, limit)
