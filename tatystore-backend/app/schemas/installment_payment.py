"""
Schemas Pydantic para InstallmentPayment
Pagamentos parciais de parcelas
"""
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, model_validator, field_serializer
from datetime import datetime
from typing import Optional
from app.models.installment_payment import InstallmentPaymentStatus
from app.core.datetime_utils import localize_to_fortaleza


class InstallmentPaymentCreate(BaseModel):
    """
    Schema para registrar um pagamento de parcela.

    Permite pagamentos parciais ou totais:
    - Deve R$ 200, paga R$ 50 -> parcial
    - Deve R$ 200, paga R$ 200 -> total
    - Deve R$ 200, paga R$ 100 depois mais R$ 100 -> dois pagamentos parciais
    """
    installment_id: int = Field(
        ...,  # Campo obrigatório
        description="ID da parcela a ser paga",
        examples=[38]
    )

    amount_paid: Optional[float] = Field(
        None,
        description="Valor a ser pago (pode ser parcial ou total)",
        gt=0,
        examples=[50.00, 100.00, 200.00]
    )

    amount: Optional[float] = Field(
        None,
        description="Valor a ser pago (compatibilidade com frontend)",
        gt=0,
        examples=[50.00, 100.00, 200.00]
    )

    @model_validator(mode='after')
    def validate_amount(self):
        """Garantir que pelo menos um dos campos de valor foi fornecido"""
        if self.amount_paid is None and self.amount is None:
            raise ValueError("É necessário fornecer 'amount' ou 'amount_paid'")

        # Se amount_paid não foi fornecido, usar amount
        if self.amount_paid is None and self.amount is not None:
            self.amount_paid = self.amount

        return self

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',  # Não aceitar campos extras
        json_schema_extra={
            "examples": [
                {
                    "installment_id": 38,
                    "amount_paid": 50.00
                },
                {
                    "installment_id": 39,
                    "amount": 100.00
                }
            ]
        }
    )


class InstallmentPaymentOut(BaseModel):
    """Schema para retornar dados de um pagamento"""
    id: int
    installment_id: int
    amount_paid: float = Field(description="Valor pago nesta transação")
    status: InstallmentPaymentStatus
    paid_at: datetime = Field(description="Data/hora do pagamento")
    created_at: datetime

    @computed_field
    @property
    def amount(self) -> float:
        """Campo computado para compatibilidade com testes antigos"""
        return self.amount_paid

    @field_serializer('paid_at', 'created_at')
    def serialize_datetime(self, value: datetime) -> datetime:
        """Converte datetimes de UTC para Fortaleza ao serializar"""
        if value is None:
            return None
        return localize_to_fortaleza(value)

    model_config = ConfigDict(from_attributes=True)


class InstallmentDetailOut(BaseModel):
    """
    Schema detalhado de uma parcela incluindo todos os pagamentos realizados.

    Retorna:
    - Informações da parcela (valor original, vencimento, status)
    - total_paid: soma de todos os pagamentos já feitos
    - remaining_amount: quanto ainda falta pagar
    - payments: lista com histórico de todos os pagamentos
    """
    id: int
    sale_id: int
    customer_id: int
    company_id: int
    installment_number: int
    amount: float = Field(description="Valor original da parcela")
    due_date: datetime
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    total_paid: float = Field(
        default=0.0,
        description="Soma total de todos os pagamentos realizados"
    )
    remaining_amount: float = Field(
        default=0.0,
        description="Valor restante a pagar (amount - total_paid)"
    )
    payments: list[dict] = Field(
        default=[],
        description="Histórico completo de pagamentos ordenado por data (mais recente primeiro)"
    )
    
    @field_serializer('due_date', 'paid_at', 'created_at')
    def serialize_datetime(self, value: datetime) -> datetime:
        """Converte datetimes de UTC para Fortaleza ao serializar"""
        if value is None:
            return None
        return localize_to_fortaleza(value)
    
    model_config = ConfigDict(from_attributes=True)
