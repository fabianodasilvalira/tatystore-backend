from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.api.deps import get_db_session, require_permission
from app.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/sales-summary", dependencies=[Depends(require_permission("reports.view"))])
async def sales_summary(
    range: str = Query(default="today", pattern="^(today|week|month|custom)$"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    now = datetime.now(timezone.utc)
    if range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif range == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif range == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = (start + timedelta(days=32)).replace(day=1)
    else:
        start = date_from or (now - timedelta(days=30))
        end = date_to or now
    svc = ReportsService(db)
    return await svc.sales_summary(start, end)

@router.get("/overdue-customers", dependencies=[Depends(require_permission("reports.view"))])
async def overdue_customers(db: AsyncSession = Depends(get_db_session)):
    svc = ReportsService(db)
    return await svc.overdue_customers()

@router.get("/low-stock", dependencies=[Depends(require_permission("reports.view"))])
async def low_stock(threshold: int = 5, db: AsyncSession = Depends(get_db_session)):
    svc = ReportsService(db)
    return await svc.low_stock(threshold)
