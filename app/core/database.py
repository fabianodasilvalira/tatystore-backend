"""
Configuração do banco de dados SQLAlchemy
Usa padrão sync e async com PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import settings

# URL async para SQLAlchemy
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Engine sincronizado
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False
    } if "sqlite" in settings.DATABASE_URL else {},
    poolclass=NullPool if "localhost" not in settings.DATABASE_URL else None,
    echo=False
)

# Engine assincronizado
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

# Sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base para os modelos
Base = declarative_base()


def get_db():
    """
    Dependência que fornece uma sessão do banco de dados sincronizada
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Dependência que fornece uma sessão do banco de dados assincronizada
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
