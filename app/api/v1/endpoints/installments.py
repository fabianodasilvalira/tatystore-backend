from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.messages import Messages
from app.models.user import User
from app.models.installment import Installment, InstallmentStatus
from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
from app.models.customer import Customer
from app.schemas.installment import InstallmentOut
from app.schemas.pagination import paginate

router = APIRouter()


def _calculate_installment_balance(installment: Installment) -> tuple[float, float]:
    """
    Calcula total pago e saldo restante de uma parcela.
    Retorna: (total_pago, saldo_restante)

    Esta é a função centralizada usada em todo o sistema para calcular saldos.

    Adicionada lógica para considerar status PAID: se a parcela está marcada como paga,
    retorna o valor total como pago e saldo zero, independentemente dos registros em installment_payments.
    Isso garante compatibilidade com parcelas legadas marcadas como pagas sem registros de pagamento.

    CHANGE: Adicionado arredondamento inteligente para evitar erros de ponto flutuante.
    Se o valor restante é menor que 0.01, é arredondado para 0 e total_paid é ajustado para amount.
    """
    if installment.status == InstallmentStatus.PAID:
        return float(installment.amount), 0.0

    # Cálculo normal baseado em pagamentos registrados
    total_paid = sum(
        float(p.amount_paid) for p in installment.payments
        if p.status == InstallmentPaymentStatus.COMPLETED
    )

    # CHANGE: Usar Decimal para evitar erro de arredondamento em ponto flutuante
    amount_decimal = Decimal(str(installment.amount))
    total_paid_decimal = Decimal(str(total_paid)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    remaining_decimal = (amount_decimal - total_paid_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Se o valor restante é menor que 0.01 (erro de arredondamento), considerar como 0
    if remaining_decimal <= Decimal('0.01') and remaining_decimal >= Decimal('0'):
        return float(total_paid_decimal), 0.0

    # Se o valor restante for negativo por erro de arredondamento, ajustar
    if remaining_decimal < 0:
        return float(amount_decimal), 0.0

    return float(total_paid_decimal), float(remaining_decimal)


def _enrich_installment_with_balance(installment: Installment) -> dict:
    """
    Converte parcela em dict e adiciona informações de saldo.
    Reutilizável para manter consistência em toda API.
    """
    data = InstallmentOut.model_validate(installment).model_dump()
    total_paid, remaining = _calculate_installment_balance(installment)
    data["total_paid"] = total_paid
    data["remaining_amount"] = remaining

    # CHANGE: Se remaining_amount é 0, o status deve ser "paid" independentemente do banco
    if remaining == 0.0:
        data["status"] = InstallmentStatus.PAID.value

    data["payments"] = [
        {
            "id": p.id,
            "amount_paid": float(p.amount_paid),
            "paid_at": p.paid_at,
            "status": p.status.value
        }
        for p in installment.payments if p.status == InstallmentPaymentStatus.COMPLETED
    ]
    data["payments_count"] = len(data["payments"])
    return data


@router.get("/filter", summary="Filtrar parcelas com múltiplos critérios")
def filter_installments(
        skip: int = 0,
        limit: Optional[int] = None,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        status_filter: Optional[str] = None,  # Suporte para ambos os nomes de parâmetro
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        overdue: Optional[bool] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Filtrar Parcelas com Múltiplos Critérios

    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    - `customer_id`: Filtrar por cliente (opcional)
    - `status` ou `status_filter`: Filtrar por status (optional: pending, paid, overdue, cancelled)
    - `start_date`: Data inicial (formato: YYYY-MM-DD)
    - `end_date`: Data final (formato: YYYY-MM-DD)
    - `overdue`: Filtrar apenas vencidas (true/false)
    """
    query = db.query(Installment).options(
        joinedload(Installment.payments)
    ).filter(
        Installment.company_id == current_user.company_id
    )

    status_value = status or status_filter
    if status_value:
        try:
            status_enum = InstallmentStatus(status_value.lower())
            query = query.filter(Installment.status == status_enum)
        except ValueError:
            raise HTTPException(400, detail=Messages.INSTALLMENT_INVALID_STATUS)

    if customer_id:
        query = query.filter(Installment.customer_id == customer_id)

    if start_date:
        query = query.filter(Installment.due_date >= start_date)

    if end_date:
        query = query.filter(Installment.due_date <= end_date)

    if overdue is True:
        today = date.today()
        query = query.filter(
            Installment.status == InstallmentStatus.OVERDUE,
            Installment.due_date < today
        )

    query = query.order_by(Installment.due_date.asc())

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        installments = query.all()
        limit = total if total > 0 else 1
    else:
        installments = query.limit(limit).all()

    installments_data = [_enrich_installment_with_balance(i) for i in installments]

    return paginate(installments_data, total, skip, limit)


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
        .options(joinedload(Installment.payments))
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

    installments_data = [_enrich_installment_with_balance(i) for i in installments]

    return paginate(installments_data, total, skip, limit)


@router.get("/", summary="Listar parcelas da empresa")
def list_installments(
        skip: int = 0,
        limit: Optional[int] = None,
        customer_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
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
    - `search`: Buscar por nome do cliente (opcional)
    """
    query = db.query(Installment).options(
        joinedload(Installment.payments),
        joinedload(Installment.customer)
    ).filter(
        Installment.company_id == current_user.company_id
    )

    if customer_id:
        query = query.filter(Installment.customer_id == customer_id)

    if status_filter:
        try:
            status_enum = InstallmentStatus(status_filter.lower())
            query = query.filter(Installment.status == status_enum)
        except ValueError:
            raise HTTPException(400, detail=Messages.INSTALLMENT_INVALID_STATUS)

    # CHANGE: Adicionado filtro de busca por nome do cliente
    if search:
        query = query.filter(
            Customer.name.ilike(f"%{search}%")
        )

    query = query.order_by(Installment.due_date.asc())

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        installments = query.all()
        limit = total if total > 0 else 1
    else:
        installments = query.limit(limit).all()

    installments_data = [_enrich_installment_with_balance(i) for i in installments]

    return paginate(installments_data, total, skip, limit)


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
        .options(joinedload(Installment.payments))
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

    installments_data = [_enrich_installment_with_balance(i) for i in installments]

    return paginate(installments_data, total, skip, limit)


@router.get("/{installment_id}", summary="Obter dados da parcela")
def get_installment(
        installment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Obter detalhes de uma parcela incluindo saldo pago e restante
    """
    installment = db.query(Installment).options(
        joinedload(Installment.payments)
    ).filter(Installment.id == installment_id).first()

    if not installment:
        raise HTTPException(status_code=404, detail=Messages.INSTALLMENT_NOT_FOUND)

    if installment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail=Messages.RESOURCE_NOT_FOUND)

    return _enrich_installment_with_balance(installment)
