#!/bin/bash

# Script para rodar todos os testes novos da Fase 2-6

echo "=========================================="
echo "TatyStore Backend - Test Suite Executor"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para executar testes
run_test_suite() {
    local suite_name=$1
    local test_file=$2
    
    echo -e "${YELLOW}Running: $suite_name${NC}"
    pytest "$test_file" -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $suite_name - PASSED${NC}"
    else
        echo -e "${RED}❌ $suite_name - FAILED${NC}"
    fi
    echo ""
}

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest não está instalado. Instalando...${NC}"
    pip install pytest
fi

echo "Running Test Suites..."
echo ""

# Fase 2 - Autenticação
run_test_suite "Fase 2: Auth Complete" "tests/test_auth_complete.py"

# Fase 3 - Usuários
run_test_suite "Fase 3: Users" "tests/test_users.py"

# Fase 4 - Clientes
run_test_suite "Fase 4: Customers Complete" "tests/test_customers_complete.py"

# Fase 5 - Validações
run_test_suite "Fase 5: Validation & Edge Cases" "tests/test_validation_edge_cases.py"

# Fase 6 - Auditoria e Performance
run_test_suite "Fase 6: Audit & Performance" "tests/test_audit_performance.py"

# Rodar TODOS os testes
echo ""
echo -e "${YELLOW}Running ALL tests for coverage...${NC}"
pytest tests/ -v --tb=short --co -q | grep "test_" | wc -l
echo ""

echo "=========================================="
echo "Test Execution Complete!"
echo "=========================================="

# Gerar relatório de cobertura
echo ""
echo -e "${YELLOW}Generating coverage report...${NC}"
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
