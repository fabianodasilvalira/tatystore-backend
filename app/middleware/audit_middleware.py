from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.models.audit_log import AuditLog
from app.core.db import AsyncSessionLocal
from app.api.deps import get_current_user

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return response
        user_id = None
        try:
            # Try header-based; if not possible, keep None
            from fastapi import Depends
            # In middleware we don't have Depends; skip strict auth re-check
        except:
            pass
        async with AsyncSessionLocal() as session:
            entry = AuditLog(
                user_id=user_id,
                endpoint=str(request.url.path),
                method=request.method,
                ip=request.client.host if request.client else "-"
            )
            session.add(entry)
            await session.commit()
        return response
