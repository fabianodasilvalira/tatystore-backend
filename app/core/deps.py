from fastapi import Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from jose import JWTError
from datetime import datetime, timezone
from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.company import Company
from app.services.security_alerts import notify_company_admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token: raise HTTPException(status_code=401, detail="Token ausente")
    try:
        payload = decode_token(token); user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = (await db.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
    if not user: raise HTTPException(status_code=401, detail="Usuário não encontrado")
    # opcional: atualizar last_login_at de forma ocasional
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return user

async def get_company_id_from_path(
    company_slug: str,
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background: BackgroundTasks = None,
):
    row = (await db.execute(select(Company).where(Company.slug==company_slug))).scalar_one_or_none()
    if not row: raise HTTPException(status_code=404, detail="Not Found")
    if row.status != "active":
        raise HTTPException(status_code=404, detail="Not Found")
    if str(row.id) != str(current_user.company_id):
        if background:
            await notify_company_admin(background, row, current_user, str(request.url.path))
        raise HTTPException(status_code=404, detail="Not Found")
    request.state.company_id = str(row.id)
    request.state.company_slug = row.slug
    request.state.user_id = str(current_user.id)
    return str(row.id)

def require_permission(code: str):
    async def _inner(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        sql = text("""
            SELECT 1 FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = :rid AND p.code = :code
            LIMIT 1
        """)
        row = (await db.execute(sql, {"rid": str(current_user.role_id), "code": code})).first()
        if not row: raise HTTPException(status_code=403, detail="Acesso negado")
        return True
    return _inner

