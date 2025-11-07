from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import update
from datetime import date
from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.models.sale import Installment

settings = get_settings()

async def mark_overdue():
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Installment)
            .where(Installment.status == "pending", Installment.due_date < date.today())
            .values(status="overdue")
        )
        await session.commit()

def setup_overdue_job(scheduler: AsyncIOScheduler):
    trigger = CronTrigger(hour=settings.overdue_job_hour, timezone=settings.scheduler_timezone)
    scheduler.add_job(mark_overdue, trigger, id="mark_overdue", replace_existing=True)
