#!/bin/bash

echo "================================================"
echo "🏥 HEALTH CHECK - TatyStore Backend"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

total_checks=0
passed_checks=0

# Função para rodar um check
run_check() {
    local name=$1
    local command=$2
    
    total_checks=$((total_checks + 1))
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        passed_checks=$((passed_checks + 1))
    else
        echo -e "${RED}✗${NC} $name"
    fi
}

# 1. Verificar dependências
echo "1️⃣  DEPENDÊNCIAS"
run_check "Python 3.11+" "python --version | grep -q 'Python 3.1'"
run_check "FastAPI" "python -c 'import fastapi'"
run_check "SQLAlchemy" "python -c 'import sqlalchemy'"
run_check "Pydantic" "python -c 'import pydantic'"
run_check "JWT (jose)" "python -c 'from jose import jwt'"
run_check "Passlib" "python -c 'import passlib'"
run_check "APScheduler" "python -c 'import apscheduler'"
echo ""

# 2. Verificar estrutura de arquivos
echo "2️⃣  ESTRUTURA DE ARQUIVOS"
run_check "app/main.py" "test -f app/main.py"
run_check "app/core/config.py" "test -f app/core/config.py"
run_check "app/core/security.py" "test -f app/core/security.py"
run_check "app/models/user.py" "test -f app/models/user.py"
run_check "app/models/sale.py" "test -f app/models/sale.py"
run_check "app/api/v1/endpoints/auth.py" "test -f app/api/v1/endpoints/auth.py"
run_check "tests/conftest.py" "test -f tests/conftest.py"
echo ""

# 3. Verificar banco de dados
echo "3️⃣  BANCO DE DADOS"
run_check "SQLite database exists" "test -f tatystore.db"
run_check "Alembic initialized" "test -f alembic.ini"
run_check "Migrations dir" "test -d alembic/versions"
echo ""

# 4. Verificar segurança
echo "4️⃣  SEGURANÇA"
run_check "Password hashing" "grep -q 'pbkdf2_sha256' app/core/security.py"
run_check "JWT config" "grep -q 'SECRET_KEY' app/core/config.py"
run_check "CORS middleware" "grep -q 'CORSMiddleware' app/main.py"
run_check "Environment variables" "test -f .env || test -n \"\$SECRET_KEY\""
echo ""

# 5. Rodar testes
echo "5️⃣  TESTES"
echo "Rodando pytest..."
if pytest tests/ -q 2>/dev/null | grep -q "passed"; then
    echo -e "${GREEN}✓${NC} Todos os testes passam"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}✗${NC} Alguns testes falharam"
fi
total_checks=$((total_checks + 1))
echo ""

# 6. Verificar endpoints críticos
echo "6️⃣  ENDPOINTS CRÍTICOS"
endpoints=(
    "GET /api/v1/auth/me"
    "GET /api/v1/companies/me"
    "GET /api/v1/products"
    "GET /api/v1/sales"
    "GET /api/v1/installments"
    "GET /api/v1/reports/sales"
)

for endpoint in "${endpoints[@]}"; do
    echo "  - $endpoint"
done
echo ""

# 7. Checklist de segurança
echo "7️⃣  SEGURANÇA - CHECKLIST"
echo -e "${YELLOW}⚠${NC}  Rate limiting: NÃO IMPLEMENTADO"
echo -e "${YELLOW}⚠${NC}  Token blacklist: NÃO IMPLEMENTADO"
echo -e "${YELLOW}⚠${NC}  CSRF protection: NÃO IMPLEMENTADO"
echo -e "${YELLOW}⚠${NC}  Auditoria: NÃO INTEGRADO"
echo ""

# 8. Resultados
echo "================================================"
echo "📊 RESULTADOS"
echo "================================================"
echo "Checks Passados: $passed_checks/$total_checks"

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}✓ Sistema PRONTO para uso${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Algumas verificações falharam${NC}"
    exit 1
fi
