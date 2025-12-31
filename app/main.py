"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import subprocess
import sys

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.seed import seed_data, ensure_platform_admin
from app.api.v1 import api_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.overdue_job import mark_overdue_installments, get_overdue_job_config
from fastapi.openapi.utils import get_openapi


import logging
from pythonjsonlogger import jsonlogger

# Configuração de Logs Estruturados (JSON)
logger = logging.getLogger()
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def init_db():
    try:
        logger.info("Executando migrações do banco de dados...")

        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()

            if "already at head" not in stderr and "target database is not up to date" not in stderr and result.returncode == 0:
                logger.info("Migrações já estão atualizadas")
            elif result.returncode == 0 and ("OK" in stdout or "success" in stdout.lower()):
                logger.info("Migrações executadas com sucesso")
            else:
                logger.warning(f"Aviso nas migrações: {stderr or stdout}")
                logger.info("Criando tabelas diretamente com SQLAlchemy (fallback)...")
                try:
                    Base.metadata.create_all(bind=engine)
                    logger.info("Tabelas criadas com sucesso (fallback)")
                except Exception as fallback_error:
                    logger.error(f"Erro no fallback: {fallback_error}")
                    raise
        else:
            logger.info("Migrações executadas com sucesso")

        logger.info("Inicializando dados do sistema...")
        db = SessionLocal()
        try:
            seed_data(db)
            ensure_platform_admin(db)  # Garantir admin do .env sempre
            logger.info("Dados do sistema inicializados com sucesso")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        import traceback
        traceback.print_exc()
        raise


if os.getenv("TESTING") != "true":
    init_db()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


async def setup_scheduler():
    try:
        scheduler = AsyncIOScheduler()

        job_config = get_overdue_job_config()
        scheduler.add_job(
            mark_overdue_installments,
            'cron',
            hour=job_config['hour'],
            minute=job_config['minute'],
            timezone=job_config['timezone'],
            id='mark_overdue_daily'
        )

        scheduler.start()
        logger.info("Scheduler iniciado com sucesso")
        return scheduler
    except Exception as e:
        logger.error(f"Erro ao iniciar scheduler: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.scheduler = await setup_scheduler()
        
        # Logs essenciais de inicialização
        logger.info("="*50)
        logger.info(f"Versão da API: {settings.VERSION}")
        logger.info(f"Total de rotas registradas: {len(app.routes)}")
        logger.info("="*50)
        logger.info("Aplicação iniciada com sucesso")
    except Exception as e:
        logger.error(f"Erro na startup: {e}")
    yield
    if hasattr(app, 'scheduler') and app.scheduler:
        try:
            app.scheduler.shutdown()
            logger.info("Scheduler encerrado")
        except Exception as e:
            logger.error(f"Erro ao encerrar scheduler: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    redirect_slashes=True,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "defaultModelsExpandDepth": -1,
    }
)

# ✅ CORS FINAL E CORRETO — LÊ DO .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# logger.info(f"CORS configurado para: {settings.BACKEND_CORS_ORIGINS}")

# Servir uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Sistema"])
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
    }


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."}
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
