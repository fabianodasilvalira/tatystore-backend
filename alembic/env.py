from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.db import Base
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission, role_permissions
from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleItem, Installment
from app.models.password_reset_token import PasswordResetToken
from app.models.login_attempt import LoginAttempt
from app.models.audit_log import AuditLog
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

