from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.login_attempt import LoginAttempt

MAX_ATTEMPTS = 5
WINDOW_MINUTES = 10
LOCK_MINUTES = 15

async def register_login_attempt(db: AsyncSession, email: str, success: bool):
    attempt = LoginAttempt(email=email, success=success)
    db.add(attempt)
    await db.commit()

async def is_account_locked(db: AsyncSession, email: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    attempts = (await db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == email, LoginAttempt.created_at >= cutoff)
        .order_by(desc(LoginAttempt.created_at))
    )).scalars().all()
    failures = [a for a in attempts if not a.success]
    if len(failures) < MAX_ATTEMPTS:
        return False
    last_fail = failures[0].created_at
    return last_fail + timedelta(minutes=LOCK_MINUTES) > datetime.now(timezone.utc)

# Alert + captcha helpers
from app.services.email_service import send_email_background
from app.core.config import get_settings
from fastapi import BackgroundTasks
settings = get_settings()

async def check_and_alert(db: AsyncSession, email: str, background: BackgroundTasks):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    attempts = (await db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == email, LoginAttempt.created_at >= cutoff)
        .order_by(desc(LoginAttempt.created_at))
    )).scalars().all()
    failures = [a for a in attempts if not a.success]
    if len(failures) == 3:
        send_email_background(
            background,
            settings.email_from,
            "Alerta de tentativas de login",
            "alert_security",
            email=email,
            count=len(failures),
            timeframe=WINDOW_MINUTES
        )

async def login_failed_twice_recently(db: AsyncSession, email: str) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    attempts = (await db.execute(
        select(LoginAttempt).where(LoginAttempt.email == email, LoginAttempt.created_at >= cutoff).order_by(desc(LoginAttempt.created_at))
    )).scalars().all()
    return len([a for a in attempts if not a.success]) >= 2
