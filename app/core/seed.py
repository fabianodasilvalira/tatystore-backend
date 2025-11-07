import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.company import Company
from app.core.security import hash_password
from app.core.config import get_settings
settings = get_settings()
PERMISSIONS = [
    ("products.view", "Pode visualizar produtos"),
    ("products.create", "Pode cadastrar novos produtos"),
    ("products.update", "Pode editar informações gerais de produtos"),
    ("products.update_stock", "Pode alterar o estoque de produtos"),
    ("customers.view", "Pode visualizar clientes"),
    ("customers.create", "Pode cadastrar novos clientes"),
    ("customers.update", "Pode editar dados de clientes"),
    ("sales.create", "Pode registrar vendas"),
    ("sales.cancel", "Pode cancelar vendas"),
    ("reports.view", "Pode visualizar relatórios"),
]
ROLES = ["Administrador", "Vendedor"]
async def seed_data(db: AsyncSession):
    per_objs=[]
    for code,desc in PERMISSIONS:
        p=(await db.execute(select(Permission).where(Permission.code==code))).scalar_one_or_none()
        if not p:
            from app.models.permission import Permission as Pm
            p=Pm(id=uuid.uuid4(), code=code, description=desc); db.add(p)
        per_objs.append(p)
    await db.flush()
    role_map={}
    for name in ROLES:
        r=(await db.execute(select(Role).where(Role.name==name))).scalar_one_or_none()
        if not r:
            from app.models.role import Role as Rl
            r=Rl(id=uuid.uuid4(), name=name); db.add(r)
        role_map[name]=r
    await db.flush()
    # assign role_permissions via raw SQL to avoid ORM relationship boilerplate
    await db.execute(text("DELETE FROM role_permissions"))
    for rname, codes in {
        "Administrador": [p.code for p in per_objs],
        "Vendedor": ["products.view","customers.view","customers.create","sales.create"],
    }.items():
        role = role_map[rname]
        for p in per_objs:
            if p.code in codes:
                await db.execute(text("INSERT INTO role_permissions(role_id, permission_id) VALUES (:r,:p) ON CONFLICT DO NOTHING"),
                                 {"r": str(role.id), "p": str(p.id)})
    taty=(await db.execute(select(Company).where(Company.slug=="taty"))).scalar_one_or_none()
    if not taty:
        taty=Company(name="Taty Perfumaria", slug="taty"); db.add(taty)
    carol=(await db.execute(select(Company).where(Company.slug=="carol"))).scalar_one_or_none()
    if not carol:
        carol=Company(name="Carol Perfumaria", slug="carol"); db.add(carol)
    await db.flush()
    admin=(await db.execute(select(User).where(User.email==settings.admin_email))).scalar_one_or_none()
    if not admin:
        admin=User(name="Administrador", email=settings.admin_email, password_hash=hash_password(settings.admin_password),
                   company_id=taty.id, role_id=role_map["Administrador"].id); db.add(admin); await db.flush()
    await db.commit()

