from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base  # Consolidando em um único arquivo - este arquivo não será mais usado

DATABASE_URL = "your_database_url_here"  # Assuming settings.DATABASE_URL is defined elsewhere

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
