from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password, verify_password
class UserService:
    def __init__(self, db: AsyncSession): self.db = db
    async def register(self, name: str, email: str, password: str, company_id: str, role_id: str):
        q = select(User).where(User.email == email)
        if (await self.db.execute(q)).scalar_one_or_none(): raise ValueError("Email já em uso")
        obj = User(name=name, email=email, password_hash=hash_password(password),
                   company_id=company_id, role_id=role_id)
        self.db.add(obj); await self.db.commit(); await self.db.refresh(obj); return obj
    async def authenticate(self, email: str, password: str):
        q = select(User).where(User.email == email); user=(await self.db.execute(q)).scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash): return None
        return user
