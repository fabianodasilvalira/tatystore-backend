from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import sys
from decimal import Decimal, ROUND_HALF_UP

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.messages import Messages
from app.models.user import User
from app.models.installment import Installment, InstallmentStatus
from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
from app.schemas.installment_payment import (
    InstallmentPaymentCreate,
    InstallmentPaymentOut,
    InstallmentDetailOut
)
from app.schemas.installment import InstallmentOut
from app.api.v1.endpoints.installments import _calculate_installment_balance

router = APIRouter()


def paginate(data: list, total: int, skip: int, limit: int) -> dict:
    """Helper para paginar respostas"""
    return {
        "items": data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }


@router.post("/", response_model=InstallmentPaymentOut, status_code=status.HTTP_201_CREATED,
             summary="Registrar pagamento de parcela")
def create_installment_payment(
        payment_data: InstallmentPaymentCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Criar Pagamento de Parcela

    **Corpo da requisição:**
    \`\`\`json
    {
        "installment_id": 1,
        "amount": 100.00,
        "payment_method": "cash"
    }
\`\`\`    """

    if not payment_data.installment_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=Messages.PAYMENT_INSTALLMENT_ID_REQUIRED
        )

    installment = db.query(Installment).filter(
        Installment.id == payment_data.installment_id
    ).first()

    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.INSTALLMENT_NOT_FOUND
        )

    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.RESOURCE_NOT_FOUND
        )

    amount = payment_data.amount_paid or payment_data.amount

    if amount is None or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O valor do pagamento deve ser maior que zero"
        )

    total_paid, remaining_amount = _calculate_installment_balance(installment)

    if remaining_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta parcela já está totalmente paga"
        )

    # CHANGE: Usar Decimal para evitar problemas de precisão com ponto flutuante
    amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    remaining_decimal = Decimal(str(remaining_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if amount_decimal > remaining_decimal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.format(Messages.PAYMENT_AMOUNT_EXCEEDS, amount=amount, remaining=remaining_amount)
        )

    db_payment = InstallmentPayment(
        installment_id=installment.id,
        amount_paid=amount,
        status=InstallmentPaymentStatus.COMPLETED,
        company_id=current_user.company_id
    )
    db.add(db_payment)

    # CHANGE: Calcula novo total após adicionar pagamento, e persiste status PAID no banco se necessário
    new_total_paid = total_paid + amount
    amount_float = float(installment.amount)

    # Usar Decimal para comparação precisa
    new_total_decimal = Decimal(str(new_total_paid)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    amount_decimal_compare = Decimal(str(amount_float)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if new_total_decimal >= amount_decimal_compare:
        installment.status = InstallmentStatus.PAID

    db.commit()
    db.refresh(db_payment)

    response = InstallmentPaymentOut.model_validate(db_payment)
    return response


@router.post("/{installment_id}/pay", response_model=InstallmentPaymentOut, status_code=status.HTTP_201_CREATED,
             summary="Registrar pagamento parcial")
def register_installment_payment(
        installment_id: int,
        payment: InstallmentPaymentCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Endpoint alternativo para registrar pagamento (mantido para compatibilidade com testes)"""

    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.INSTALLMENT_NOT_FOUND
        )

    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.RESOURCE_NOT_FOUND
        )

    amount = payment.amount_paid or payment.amount

    if amount is None or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O valor do pagamento deve ser maior que zero"
        )

    total_paid, remaining_amount = _calculate_installment_balance(installment)

    if remaining_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta parcela já está totalmente paga"
        )

    # CHANGE: Usar Decimal para evitar problemas de precisão com ponto flutuante
    amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    remaining_decimal = Decimal(str(remaining_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if amount_decimal > remaining_decimal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.format(Messages.PAYMENT_AMOUNT_EXCEEDS, amount=amount, remaining=remaining_amount)
        )

    db_payment = InstallmentPayment(
        installment_id=installment_id,
        amount_paid=amount,
        status=InstallmentPaymentStatus.COMPLETED,
        company_id=current_user.company_id
    )
    db.add(db_payment)

    # CHANGE: Calcula novo total após adicionar pagamento, e persiste status PAID no banco se necessário
    new_total_paid = total_paid + amount
    amount_float = float(installment.amount)

    # Usar Decimal para comparação precisa
    new_total_decimal = Decimal(str(new_total_paid)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    amount_decimal_compare = Decimal(str(amount_float)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if new_total_decimal >= amount_decimal_compare:
        installment.status = InstallmentStatus.PAID

    db.commit()
    db.refresh(db_payment)

    return InstallmentPaymentOut.model_validate(db_payment)


@router.get("/installments/{installment_id}/payments", summary="Listar pagamentos de uma parcela")
def list_installment_payments(
        installment_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Listar Histórico de Pagamentos de uma Parcela

    **Parâmetros:**
    - `skip`: Quantidade de registros a pular (padrão: 0)
    - `limit`: Quantidade máxima de registros (padrão: 100, máximo: 1000)
    """
    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.INSTALLMENT_NOT_FOUND
        )

    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.RESOURCE_NOT_FOUND
        )

    query = db.query(InstallmentPayment).filter(
        InstallmentPayment.installment_id == installment_id
    ).order_by(InstallmentPayment.paid_at.desc())

    total = query.count()
    payments = query.offset(skip).limit(limit).all()

    payments_data = [InstallmentPaymentOut.model_validate(p).model_dump() for p in payments]

    return paginate(payments_data, total, skip, limit)


@router.get("/installments/{installment_id}/detail", response_model=InstallmentDetailOut,
            summary="Obter detalhes completos da parcela")
def get_installment_detail(
        installment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Obter Detalhes Completos da Parcela

    Retorna informações da parcela incluindo:
    - Dados básicos da parcela
    - Total pago até o momento
    - Valor restante a pagar
    - Histórico completo de pagamentos

    CHANGE: Agora retorna remaining_amount corretamente arredondado.
    Se a parcela está totalmente paga, remaining_amount = 0.0 e status = "paid"
    """
    installment = db.query(Installment).filter(
        Installment.id == installment_id
    ).first()

    if not installment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.INSTALLMENT_NOT_FOUND
        )

    if installment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.RESOURCE_NOT_FOUND
        )

    total_paid, remaining_amount = _calculate_installment_balance(installment)

    payments = db.query(InstallmentPayment).filter(
        InstallmentPayment.installment_id == installment_id
    ).order_by(InstallmentPayment.paid_at.desc()).all()

    payments_data = [InstallmentPaymentOut.model_validate(p).model_dump() for p in payments]

    # CHANGE: Se remaining_amount é 0, o status deve ser "paid" independentemente do banco
    response_status = installment.status.value
    if remaining_amount == 0.0:
        response_status = InstallmentStatus.PAID.value

    return InstallmentDetailOut(
        id=installment.id,
        sale_id=installment.sale_id,
        customer_id=installment.customer_id,
        company_id=installment.company_id,
        installment_number=installment.installment_number,
        amount=float(installment.amount),
        due_date=installment.due_date,
        status=response_status,
        paid_at=installment.paid_at,
        created_at=installment.created_at,
        total_paid=total_paid,
        remaining_amount=remaining_amount,
        payments=payments_data
    )


@router.get("/", summary="Listar todos os pagamentos de parcelas")
def list_all_payments(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        installment_id: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Listar Todos os Pagamentos de Parcelas da Empresa

    **Parâmetros:**
    - `skip`: Quantidade de registros a pular (padrão: 0)
    - `limit`: Quantidade máxima de registros (padrão: 100, máximo: 1000)
    - `installment_id`: Filtrar por parcela específica (opcional)
    """
    query = db.query(InstallmentPayment).filter(
        InstallmentPayment.company_id == current_user.company_id
    )

    if installment_id:
        query = query.filter(InstallmentPayment.installment_id == installment_id)

    query = query.order_by(InstallmentPayment.paid_at.desc())

    total = query.count()
    payments = query.offset(skip).limit(limit).all()

    payments_data = [InstallmentPaymentOut.model_validate(p).model_dump() for p in payments]

    return paginate(payments_data, total, skip, limit)


@router.get("/{payment_id}", response_model=InstallmentPaymentOut, summary="Obter detalhes de um pagamento")
def get_payment_detail(
        payment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Obter Detalhes de um Pagamento Específico
    """
    payment = db.query(InstallmentPayment).filter(
        InstallmentPayment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado"
        )

    if payment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.RESOURCE_NOT_FOUND
        )

    return InstallmentPaymentOut.model_validate(payment)
