from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from slowapi.middleware import SlowAPIMiddleware
from app.middleware.rate_limit import limiter, tenant_key
from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.core.seed import seed_data
from app.api import auth, products, customers, sales, installments, reports
from app.middleware.audit_middleware import AuditMiddleware
from app.jobs.overdue_job import setup_overdue_job
settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware, key_func=tenant_key)
app.add_middleware(AuditMiddleware)
app.include_router(auth.router)  # /auth/*
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(sales.router)
app.include_router(installments.router)
app.include_router(reports.router)
scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
@app.on_event("startup")
async def on_startup():
    setup_overdue_job(scheduler); scheduler.start()
    async with AsyncSessionLocal() as session: await seed_data(session)
@app.on_event("shutdown")
async def on_shutdown():
    if scheduler.running: scheduler.shutdown(wait=False)

