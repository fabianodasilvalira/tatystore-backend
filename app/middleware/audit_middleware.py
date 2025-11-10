from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        try:
            async with AsyncSessionLocal() as db:
                uid = getattr(getattr(request, "state", object()), "user_id", None)
                cid = getattr(getattr(request, "state", object()), "company_id", None)
                log = AuditLog(user_id=uid, company_id=cid, action=f"HTTP {request.method}", endpoint=request.url.path, method=request.method, ip=(request.client.host if request.client else "-"))
                db.add(log); await db.commit()
        except Exception:
            pass
        return response
