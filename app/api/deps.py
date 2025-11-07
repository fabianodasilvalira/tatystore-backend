from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from jose import JWTError
from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

def require_permission(code: str):
    async def _inner(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        sql = text("""
            SELECT 1
            FROM permissions p
            JOIN role_permissions rp ON rp.permission_id = p.id
            JOIN user_roles ur ON ur.role_id = rp.role_id
            WHERE ur.user_id = :uid AND p.code = :code
            LIMIT 1
        """)
        row = (await db.execute(sql, {"uid": str(current_user.id), "code": code})).first()
        if not row:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return current_user
    return _inner
