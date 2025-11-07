from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
limiter = Limiter(key_func=get_remote_address)
async def tenant_key(request: Request):
    slug = request.path_params.get("company_slug") or "public"
    return f"tenant:{slug}"

