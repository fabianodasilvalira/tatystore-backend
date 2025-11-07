import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.core.security import hash_password

PERMISSIONS = [
    ("products.view", "Pode listar e visualizar produtos"),
    ("products.manage", "Pode criar/editar produtos"),
    ("sales.create", "Pode registrar vendas"),
    ("sales.cancel", "Pode cancelar vendas"),
    ("reports.view", "Pode visualizar relatórios"),
]

ROLES = ["Administrador", "Vendedor"]

async def seed_data(db: AsyncSession):
    # Permissões
    perm_objs = []
    for code, desc in PERMISSIONS:
        p = (await db.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
        if not p:
            from app.models.permission import Permission as Pm
            p = Pm(id=uuid.uuid4(), code=code, description=desc)
            db.add(p)
        perm_objs.append(p)
    await db.flush()

    # Roles
    role_map = {}
    for name in ROLES:
        r = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
        if not r:
            from app.models.role import Role as Rl
            r = Rl(id=uuid.uuid4(), name=name)
            db.add(r)
        role_map[name] = r
    await db.flush()

    admin = role_map["Administrador"]
    vendedor = role_map["Vendedor"]
    admin.permissions = perm_objs
    vendedor.permissions = [p for p in perm_objs if p.code in ("products.view","sales.create")]
    await db.flush()

    # Admin user
    admin_user = (await db.execute(select(User).where(User.email=="admin@local"))).scalar_one_or_none()
    if not admin_user:
        admin_user = User(id=uuid.uuid4(), name="Administrador do Sistema", email="admin@local",
                          password_hash=hash_password("admin@2025"))
        db.add(admin_user)
        await db.flush()
        admin_user.roles.append(admin)

    await db.commit()
