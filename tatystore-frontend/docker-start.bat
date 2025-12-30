@echo off
REM Script de inicialização rápida para TatyStore com Docker (Windows)
REM Este script facilita a configuração inicial do projeto

echo.
echo 🚀 Iniciando configuração do TatyStore com Docker...
echo.

REM Verifica se Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não está instalado. Por favor, instale o Docker primeiro.
    echo    Visite: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Verifica se Docker Compose está instalado
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro.
    echo    Visite: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker e Docker Compose estão instalados
echo.

REM Verifica se o arquivo .env existe
if not exist .env (
    echo 📝 Criando arquivo .env a partir do .env.example...
    copy .env.example .env >nul
    echo ⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua GEMINI_API_KEY
    echo.
    pause
) else (
    echo ✅ Arquivo .env já existe
)

echo.
echo Escolha o modo de execução:
echo 1^) Desenvolvimento ^(hot-reload, porta 3000^)
echo 2^) Produção ^(Nginx, porta 80^)
echo.
set /p choice="Digite sua escolha (1 ou 2): "

if "%choice%"=="1" (
    echo.
    echo 🔨 Iniciando modo DESENVOLVIMENTO...
    echo    Acesse a aplicação em: http://localhost:3000
    echo.
    docker-compose up tatystore-dev
) else if "%choice%"=="2" (
    echo.
    echo 🏭 Iniciando modo PRODUÇÃO...
    echo    Acesse a aplicação em: http://localhost
    echo.
    docker-compose up tatystore-prod
) else (
    echo ❌ Opção inválida. Execute o script novamente.
    pause
    exit /b 1
)
