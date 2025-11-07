from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.core.seed import seed_data
from app.api import auth, products, customers, sales, installments, reports
from app.middleware.audit_middleware import AuditMiddleware
from app.jobs.overdue_job import setup_overdue_job
from app.jobs.refresh_materialized_views import refresh_materialized_views

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(installments.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

# Scheduler
scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

@app.on_event("startup")
async def on_startup():
    setup_overdue_job(scheduler)
    scheduler.add_job(refresh_materialized_views, "cron", minute=0, id="refresh_mv", replace_existing=True)
    scheduler.start()
    async with AsyncSessionLocal() as session:
        await seed_data(session)

@app.on_event("shutdown")
async def on_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)
