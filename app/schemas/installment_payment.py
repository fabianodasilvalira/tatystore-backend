"""
Schemas Pydantic para InstallmentPayment
Pagamentos parciais de parcelas
"""
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, model_validator
from datetime import datetime
from typing import Optional
from app.models.installment_payment import InstallmentPaymentStatus


class InstallmentPaymentCreate(BaseModel):
    """Schema para registrar um pagamento parcial"""
    installment_id: Optional[int] = None

    amount_paid: Optional[float] = None
    amount: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, extra='allow')

    @model_validator(mode='after')
    def validate_amount(self):
        """Valida que pelo menos um valor de pagamento foi fornecido e é válido"""
        # Tenta amount_paid primeiro, depois amount
        if self.amount_paid is not None:
            payment_amount = self.amount_paid
        elif self.amount is not None:
            payment_amount = self.amount
            # Normalizar: copiar amount para amount_paid para consistência interna
            self.amount_paid = self.amount
        else:
            # Nenhum fornecido
            raise ValueError('É necessário fornecer "amount_paid" ou "amount"')

        # Valida se é maior que zero
        if payment_amount <= 0:
            raise ValueError('O valor do pagamento deve ser maior que zero')

        return self


class InstallmentPaymentOut(BaseModel):
    """Schema para retornar dados de pagamento"""
    id: int
    installment_id: int
    amount_paid: float
    status: InstallmentPaymentStatus
    paid_at: datetime
    created_at: datetime
    
    @computed_field
    @property
    def amount(self) -> float:
        """Campo computado para compatibilidade com testes"""
        return self.amount_paid
    
    model_config = ConfigDict(from_attributes=True)


class InstallmentDetailOut(BaseModel):
    """Schema detalhado de parcela com histórico de pagamentos"""
    id: int
    sale_id: int
    customer_id: int
    company_id: int
    installment_number: int
    amount: float  # Valor original da parcela
    due_date: datetime
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime
    
    total_paid: float = 0.0  # Soma de todos os pagamentos
    remaining_amount: float = 0.0  # Valor ainda não pago
    payments: list[dict] = []  # Histórico de pagamentos
    
    model_config = ConfigDict(from_attributes=True)
