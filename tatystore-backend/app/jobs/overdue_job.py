"""
Job agendado para marcar parcelas vencidas como overdue
Executado diariamente via cron
"""
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.installment import Installment, InstallmentStatus


async def mark_overdue_installments():
    """
    Marca todas as parcelas vencidas (due_date < hoje) como overdue
    Executado diariamente
    """
    async with AsyncSessionLocal() as session:
        # Buscar todas as parcelas pendentes com vencimento anterior ao dia atual
        today = date.today()
        
        stmt = update(Installment).where(
            Installment.status == InstallmentStatus.PENDING,
            Installment.due_date < today
        ).values(
            status=InstallmentStatus.OVERDUE
        )
        
        await session.execute(stmt)
        await session.commit()


def get_overdue_job_config():
    """
    Retorna configuração do cron job
    Hora padrão: 00:00 UTC (pode ser customizada via OVERDUE_JOB_HOUR)
    """
    return {
        "hour": getattr(settings, 'OVERDUE_JOB_HOUR', 0),
        "minute": 0,
        "timezone": getattr(settings, 'SCHEDULER_TIMEZONE', 'UTC')
    }
