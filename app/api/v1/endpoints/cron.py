"""
Endpoints de Cron Jobs (v1)
Tarefas agendadas do sistema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.core.deps import verify_cron_auth
from app.models.installment import Installment, InstallmentStatus
from app.models.company import Company  # Added import for Company model
from app.models.installment_payment import InstallmentPaymentStatus  # Added import for InstallmentPaymentStatus

router = APIRouter()


@router.post("/mark-overdue", summary="Marcar parcelas vencidas (CRON)")
async def mark_overdue(
    cron_auth: bool = Depends(verify_cron_auth),
    db: Session = Depends(get_db)
):
    """
    **Marcar Parcelas como Vencidas**
    
    Job executado diariamente para atualizar status de parcelas vencidas.
    
    **Autenticação:** Header `X-Cron-Secret` obrigatório
    """
    today = date.today()
    
    pending_overdue = db.query(Installment).filter(
        Installment.due_date < today,
        Installment.status == InstallmentStatus.PENDING
    ).all()
    
    updated_count = 0
    for installment in pending_overdue:
        installment.status = InstallmentStatus.OVERDUE
        updated_count += 1
    
    db.commit()
    
    return {
        "message": "Parcelas vencidas atualizadas",
        "updated_count": updated_count,
        "executed_at": str(date.today())
    }


@router.post("/mark-overdue-installments", summary="Marcar parcelas vencidas (CRON)")
async def mark_overdue_installments(
    cron_auth: bool = Depends(verify_cron_auth),
    db: Session = Depends(get_db)
):
    """
    **Marcar Parcelas como Vencidas**
    
    Job executado diariamente para atualizar status de parcelas vencidas.
    
    **Autenticação:** Header `X-Cron-Secret` obrigatório
    """
    today = date.today()
    
    pending_overdue = db.query(Installment).filter(
        Installment.due_date < today,
        Installment.status == InstallmentStatus.PENDING
    ).all()
    
    updated_count = 0
    for installment in pending_overdue:
        installment.status = InstallmentStatus.OVERDUE
        updated_count += 1
    
    db.commit()
    
    return {
        "message": "Parcelas vencidas atualizadas",
        "updated_count": updated_count,
        "executed_at": str(date.today())
    }


@router.get("/overdue-summary", summary="Resumo de inadimplência")
async def overdue_summary(
    cron_auth: bool = Depends(verify_cron_auth),
    db: Session = Depends(get_db)
):
    """
    **Resumo de Inadimplência por Empresa**
    
    Retorna sumário de parcelas vencidas agrupadas por empresa.
    Considera apenas saldo restante após pagamentos parciais.
    """
    overdue_installments = db.query(Installment).filter(
        Installment.status == InstallmentStatus.OVERDUE
    ).all()
    
    def _calculate_remaining_amount(installment: Installment) -> float:
        total_paid = sum(
            p.amount_paid for p in installment.payments 
            if p.status == InstallmentPaymentStatus.COMPLETED
        )
        return max(0, installment.amount - total_paid)
    
    # Agrupar por empresa
    companies_data = {}
    total_overdue_amount = 0.0
    
    for installment in overdue_installments:
        remaining = _calculate_remaining_amount(installment)
        company_id = installment.company_id
        
        if company_id not in companies_data:
            companies_data[company_id] = {
                "count": 0,
                "total_amount": 0.0
            }
        companies_data[company_id]["count"] += 1
        companies_data[company_id]["total_amount"] += remaining
        total_overdue_amount += remaining
    
    # Preencher informações de empresa
    companies = []
    for company_id, data in companies_data.items():
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            companies.append({
                "company_id": company_id,
                "company_name": company.name,
                "overdue_count": data["count"],
                "overdue_amount": round(data["total_amount"], 2)
            })
    
    return {
        "companies": companies,
        "total_companies": len(companies),
        "total_overdue_installments": len(overdue_installments),
        "total_overdue_amount": round(total_overdue_amount, 2),
        "generated_at": str(date.today())
    }


@router.get("/health", summary="Health check do cron")
async def cron_health():
    """
    **Health Check**
    
    Verifica se o sistema de cron está respondendo.
    """
    return {
        "status": "healthy",
        "cron_service": "running"
    }
