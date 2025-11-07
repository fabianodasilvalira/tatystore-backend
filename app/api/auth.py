from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timezone
from app.api.deps import get_db_session, get_current_user
from app.schemas.user_schemas import UserCreate, UserOut
from app.services.user_service import UserService
from app.core.security import create_access_token, verify_password, hash_password
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.captcha_challenge import CaptchaChallenge
from app.services.email_service import send_email_background
from app.services.security_service import register_login_attempt, is_account_locked, check_and_alert, login_failed_twice_recently

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db_session)):
    svc = UserService(db)
    try:
        user = await svc.register(payload.name, payload.email, payload.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), background: BackgroundTasks = None, db: AsyncSession = Depends(get_db_session)):
    email = form.username
    if await is_account_locked(db, email):
        raise HTTPException(status_code=429, detail="Conta temporariamente bloqueada. Tente novamente mais tarde.")
    svc = UserService(db)
    user = await svc.authenticate(email, form.password)
    if not user:
        await register_login_attempt(db, email, False)
        if background:
            await check_and_alert(db, email, background)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    await register_login_attempt(db, email, True)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "Bearer"}

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

@router.put("/change-password")
async def change_password(payload: ChangePasswordIn, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    current_user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"detail": "Senha alterada com sucesso"}

class ForgotPasswordIn(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordIn, background: BackgroundTasks, db: AsyncSession = Depends(get_db_session)):
    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if not user:
        return {"detail": "Se o email existir, enviaremos instruções."}
    token = PasswordResetToken.new(user.id)
    db.add(token); await db.commit()
    reset_link = f"http://localhost:5173/reset-password/{token.token}"
    send_email_background(background, user.email, "Redefinição de Senha", "reset_password", reset_link=reset_link)
    return {"detail": "Se o email existir, enviaremos instruções."}

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
async def reset_password(data: ResetPasswordIn, db: AsyncSession = Depends(get_db_session)):
    token = (await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == data.token))).scalar_one_or_none()
    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    user = await db.get(User, token.user_id)
    user.password_hash = hash_password(data.new_password)
    await db.delete(token); await db.commit()
    return {"detail": "Senha alterada com sucesso!"}

@router.get("/captcha")
async def get_captcha(db: AsyncSession = Depends(get_db_session)):
    challenge, question = CaptchaChallenge.new()
    db.add(challenge); await db.commit()
    return {"captcha_key": challenge.key, "question": question}

class LoginWithCaptcha(BaseModel):
    username: str
    password: str
    captcha_key: str | None = None
    captcha_answer: str | None = None

@router.post("/login-captcha")
async def login_with_captcha(data: LoginWithCaptcha, background: BackgroundTasks, db: AsyncSession = Depends(get_db_session)):
    email = data.username
    if await login_failed_twice_recently(db, email):
        if not data.captcha_key or not data.captcha_answer:
            raise HTTPException(status_code=403, detail="Captcha necessário")
        from sqlalchemy import select
        challenge = (await db.execute(select(CaptchaChallenge).where(CaptchaChallenge.key == data.captcha_key))).scalar_one_or_none()
        from datetime import datetime, timezone
        if not challenge or challenge.expires_at < datetime.now(timezone.utc) or challenge.answer != data.captcha_answer:
            raise HTTPException(status_code=403, detail="Captcha inválido/expirado")
        await db.delete(challenge); await db.commit()
    svc = UserService(db)
    user = await svc.authenticate(email, data.password)
    if not user:
        await register_login_attempt(db, email, False)
        await check_and_alert(db, email, background)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    await register_login_attempt(db, email, True)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "Bearer"}
