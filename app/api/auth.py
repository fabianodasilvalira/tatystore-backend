from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timezone
from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.user_schemas import UserCreate, UserOut
from app.services.user_service import UserService
from app.core.security import create_access_token, verify_password, hash_password
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.services.email_service import send_email_background
router = APIRouter(prefix="/auth", tags=["Auth"])
@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    svc = UserService(db)
    try:
        obj = await svc.register(payload.name, payload.email, payload.password,
                                 company_id=current_user.company_id, role_id=current_user.role_id)
        return obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    svc = UserService(db); user = await svc.authenticate(form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "Bearer"}
class ChangePasswordIn(BaseModel): old_password: str; new_password: str
@router.put("/change-password")
async def change_password(payload: ChangePasswordIn, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    current_user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"detail": "Senha alterada com sucesso"}
class ForgotPasswordIn(BaseModel): email: str
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordIn, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user=(await db.execute(select(User).where(User.email==data.email))).scalar_one_or_none()
    if not user: return {"detail":"Se o email existir, enviaremos instruções."}
    token=PasswordResetToken.new(user.id); db.add(token); await db.commit()
    reset_link=f"http://localhost:5173/reset-password/{token.token}"
    send_email_background(background, user.email, "Redefinição de Senha", "reset_password", reset_link=reset_link)
    return {"detail":"Se o email existir, enviaremos instruções."}
class ResetPasswordIn(BaseModel): token: str; new_password: str
@router.post("/reset-password")
async def reset_password(data: ResetPasswordIn, db: AsyncSession = Depends(get_db)):
    token=(await db.execute(select(PasswordResetToken).where(PasswordResetToken.token==data.token))).scalar_one_or_none()
    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    user=await db.get(User, token.user_id)
    user.password_hash=hash_password(data.new_password)
    await db.delete(token); await db.commit()
    return {"detail":"Senha alterada com sucesso!"}

