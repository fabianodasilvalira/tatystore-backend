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
from app.core.seed import seed_data
from app.api.v1 import api_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.overdue_job import mark_overdue_installments, get_overdue_job_config
from fastapi.openapi.utils import get_openapi

def init_db():
    """
    Inicializar banco de dados - executar migrações com Alembic
    Migrações precisam rodar antes do seed_data
    """
    try:
        print("🔄 Executando migrações do banco de dados...")

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
                print("✓ Migrações já estão atualizadas")
            elif result.returncode == 0 and ("OK" in stdout or "success" in stdout.lower()):
                print("✓ Migrações executadas com sucesso")
            else:
                print(f"⚠️  Aviso nas migrações: {stderr or stdout}")
                print("🔄 Criando tabelas diretamente com SQLAlchemy (fallback)...")
                try:
                    Base.metadata.create_all(bind=engine)
                    print("✓ Tabelas criadas com sucesso (fallback)")
                except Exception as fallback_error:
                    print(f"✗ Erro no fallback: {fallback_error}")
                    raise
        else:
            print("✓ Migrações executadas com sucesso")

        print("🌱 Inicializando dados do sistema...")
        db = SessionLocal()
        try:
            seed_data(db)
            print("✓ Dados do sistema inicializados com sucesso")
        finally:
            db.close()

    except Exception as e:
        print(f"✗ Erro ao inicializar banco: {e}")
        import traceback
        traceback.print_exc()
        raise

if os.getenv("TESTING") != "true":
    init_db()

# Criar diretórios de upload
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

async def setup_scheduler():
    """Setup scheduler para rodar jobs agendados"""
    try:
        scheduler = AsyncIOScheduler()

        # Registrar job de parcelas vencidas
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
        print("✓ Scheduler iniciado com sucesso")
        return scheduler
    except Exception as e:
        print(f"✗ Erro ao iniciar scheduler: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Use modern lifespan context manager instead of @app.on_event
    Manage startup and shutdown events
    """
    # Startup
    try:
        app.scheduler = await setup_scheduler()
        print("✓ Aplicação iniciada com sucesso")
    except Exception as e:
        print(f"✗ Erro na startup: {e}")

    yield

    # Shutdown
    if hasattr(app, 'scheduler') and app.scheduler:
        try:
            app.scheduler.shutdown()
            print("✓ Scheduler encerrado")
        except Exception as e:
            print(f"✗ Erro ao encerrar scheduler: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## TatyStore Backend - Sistema Multi-Empresa
    
    Sistema completo de gestão comercial com suporte a múltiplas empresas.
    
    ### Funcionalidades:
    - ✓ Autenticação JWT com isolamento por empresa
    - ✓ Gestão de Produtos e Estoque
    - ✓ Vendas (À Vista e Crediário)
    - ✓ Clientes
    - ✓ Parcelas com atualização automática
    - ✓ Relatórios Completos
    - ✓ Integração PIX
    - ✓ Rotas Públicas para Visitantes
    
    ### 🔐 Como Autenticar no Swagger:
    
    **Passo 1:** Faça login em **POST /api/v1/auth/login** com as credenciais abaixo
    **Passo 2:** Copie o valor do campo **"access_token"** da resposta
    **Passo 3:** Clique no botão **"Authorize" 🔓** no topo da página
    **Passo 4:** Cole o token no campo (NÃO precisa adicionar "Bearer", é automático)
    **Passo 5:** Clique em **"Authorize"** e feche o modal
    **Passo 6:** Agora todas as rotas protegidas funcionarão! ✅
    
    ### 👤 Credenciais Padrão (Já Pré-preenchidas):
    
    **Empresa Taty:**
    - 🔑 Admin: **admin@taty.com** / **admin123**
    - 👔 Gerente: **gerente@taty.com** / **gerente123**
    - 🛒 Vendedor: **vendedor@taty.com** / **vendedor123**
    
    **Empresa Carol:**
    - 🔑 Admin: **admin@carol.com** / **admin123**
    - 👔 Gerente: **gerente@carol.com** / **gerente123**
    - 🛒 Vendedor: **vendedor@carol.com** / **vendedor123**
    
    ### 💡 Dica:
    As credenciais já vêm pré-preenchidas no endpoint de login para facilitar os testes!
    """,
    openapi_tags=[
        {"name": "Autenticação", "description": "Login e gerenciamento de sessão"},
        {"name": "Empresas", "description": "Cadastro e gestão de empresas"},
        {"name": "Usuários", "description": "Gestão de usuários do sistema"},
        {"name": "Produtos", "description": "Catálogo e controle de estoque"},
        {"name": "Clientes", "description": "Cadastro de clientes"},
        {"name": "Vendas", "description": "Vendas à vista e crediário"},
        {"name": "Parcelas", "description": "Gestão de parcelas e crediário"},
        {"name": "Relatórios", "description": "Relatórios gerenciais"},
        {"name": "PIX", "description": "Integração de pagamento PIX"},
        {"name": "Público", "description": "Rotas sem autenticação"},
        {"name": "Cron", "description": "Tarefas agendadas"},
    ],
    lifespan=lifespan,
    redirect_slashes=False,
    swagger_ui_parameters={
        "persistAuthorization": True,  # Mantém o token após refresh
        "defaultModelsExpandDepth": -1,  # Oculta schemas por padrão
    }
)

cors_origins = settings.BACKEND_CORS_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [cors_origins]

# Adicionar middleware CORS ANTES de qualquer outra rota
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Lista de origens permitidas
    allow_credentials=True,  # Permite envio de cookies e headers de autenticação
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Métodos HTTP permitidos
    allow_headers=["*"],  # Permite todos os headers
    expose_headers=["*"],  # Expõe todos os headers na resposta
    max_age=3600,  # Cache de preflight requests por 1 hora
)

print(f"✓ CORS configurado para as origens: {cors_origins}")

# Servir arquivos de upload
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Incluir rotas da API
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Sistema"])
async def root():
    """
    **Endpoint raiz do sistema**

    Retorna informações básicas sobre o sistema.
    """
    return {
        "message": "TatyStore Backend API",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "online"
    }

@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    **Health Check**

    Verifica se o sistema está funcionando corretamente.
    """
    return {"status": "healthy"}

# Handler de erros global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor. Entre em contato com o suporte.",
            "error": str(exc) if settings.DEBUG else None
        }
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Cole o token JWT aqui (o prefixo 'Bearer' será adicionado automaticamente)"
        }
    }

    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        if "LoginRequest" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["LoginRequest"]["example"] = {
                "email": "admin@taty.com",
                "password": "admin123"
            }

    for path in openapi_schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                # Se a rota retorna 401, adicionar segurança
                if operation.get("responses", {}).get("401"):
                    operation["security"] = [{"Bearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
