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

@router.get("/overdue", response_model=List[dict], summary="Listar parcelas vencidas")
def list_overdue_installments(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Parcelas Vencidas**
    
    Lista todas as parcelas com status overdue da empresa.
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Resposta:** Lista de parcelas
    """
    today = date.today()
    
    query = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.status == InstallmentStatus.OVERDUE,
        Installment.due_date < today
    ).order_by(Installment.due_date.asc())
    
    installments = query.offset(skip).limit(limit).all()
    
    installments_data = [InstallmentResponse.model_validate(inst).model_dump() for inst in installments]
    
    return installments_data

@router.get("/overdue/list", response_model=List[dict], summary="Listar parcelas vencidas")
def list_overdue_installments_old(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Parcelas Vencidas**
    
    Lista todas as parcelas com status overdue da empresa.
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Resposta:** Lista de parcelas
    """
    today = date.today()
    
    query = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.status == InstallmentStatus.OVERDUE,
        Installment.due_date < today
    ).order_by(Installment.due_date.asc())
    
    installments = query.offset(skip).limit(limit).all()
    
    installments_data = [InstallmentResponse.model_validate(inst).model_dump() for inst in installments]
    
    return installments_data

@router.get("/", response_model=List[dict], summary="Listar parcelas da empresa")
def list_installments(
    skip: int = 0,
    limit: int = 10,
    customer_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Parcelas da Empresa**
    
    Lista todas as parcelas com filtros opcionais.
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Filtros:**
    - `customer_id`: Filtrar por cliente
    - `status_filter`: pending, paid, overdue, cancelled
    
    **Resposta:** Lista de parcelas
    """
    query = db.query(Installment).filter(
        Installment.company_id == current_user.company_id
    )
    
    if customer_id:
        query = query.filter(Installment.customer_id == customer_id)
    
    if status_filter:
        query = query.filter(Installment.status == status_filter)
    
    query = query.order_by(Installment.due_date.asc())
    
    installments = query.offset(skip).limit(limit).all()
    
    installments_data = [InstallmentResponse.model_validate(inst).model_dump() for inst in installments]
    
    return installments_data

@router.get("/{installment_id}", response_model=InstallmentResponse, summary="Obter dados da parcela")
def get_installment(
    installment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados de uma Parcela**
    
    Retorna informações detalhadas de uma parcela.
    """
    installment = db.query(Installment).filter(Installment.id == installment_id).first()
    
    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcela não encontrada"
        )
    
    # Verificar isolamento
    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    return installment

@router.patch("/{installment_id}/pay", response_model=InstallmentResponse, summary="Marcar parcela como paga")
def pay_installment(
    installment_id: int,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Marcar Parcela como Paga**
    
    Registra o pagamento de uma parcela.
    
    **Requer:** Admin ou Gerente
    """
    installment = db.query(Installment).filter(Installment.id == installment_id).first()
    
    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcela não encontrada"
        )
    
    # Verificar isolamento
    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    if installment.status == InstallmentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parcela já foi paga"
        )
    
    if installment.status == InstallmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parcela foi cancelada"
        )
    
    installment.status = InstallmentStatus.PAID
    installment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(installment)
    
    return installment

@router.get("/customer/{customer_id}", response_model=List[dict], summary="Listar parcelas do cliente")
def list_installments_by_customer(
    customer_id: int,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Parcelas por Cliente**
    
    Lista todas as parcelas de um cliente específico.
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Resposta:** Lista de parcelas
    """
    query = db.query(Installment).filter(
        Installment.company_id == current_user.company_id,
        Installment.customer_id == customer_id
    ).order_by(Installment.due_date.asc())
    
    installments = query.offset(skip).limit(limit).all()
    
    installments_data = [InstallmentResponse.model_validate(inst).model_dump() for inst in installments]
    
    return installments_data
