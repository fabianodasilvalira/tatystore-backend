"""Teste manual para diagnosticar o erro 422 do schema"""
from app.schemas.installment_payment import InstallmentPaymentCreate
import json

# Simula o payload que o teste está enviando
payload = {"amount": 100.0}

print(f"[TEST] Payload: {payload}")

try:
    # Tenta criar o objeto Pydantic
    payment = InstallmentPaymentCreate(**payload)
    print(f"[TEST] SUCCESS! Objeto criado: {payment}")
    print(f"[TEST] amount_paid={payment.amount_paid}, amount={payment.amount}")
    print(f"[TEST] installment_id={payment.installment_id}")
except Exception as e:
    print(f"[TEST] ERROR! {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
