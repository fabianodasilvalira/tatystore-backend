#!/bin/bash

# Script para executar testes do sistema de pagamentos parciais
# Uso: ./scripts/run_tests.sh [opção]

set -e

echo "=========================================="
echo "Sistema de Testes - Pagamentos Parciais"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir com cor
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar dependências
print_status "Verificando dependências..."
if ! command -v python &> /dev/null; then
    print_error "Python não encontrado!"
    exit 1
fi

if ! python -m pip show pytest > /dev/null; then
    print_warning "pytest não instalado. Instalando..."
    pip install pytest pytest-cov pytest-asyncio httpx
fi

print_success "Dependências ok"
echo ""

# Menu de opções
case "${1:-all}" in
    all)
        print_status "Executando TODOS os testes..."
        pytest tests/ -v --tb=short
        ;;
    
    fast)
        print_status "Executando testes rápidos (sem cov)..."
        pytest tests/ -v -x
        ;;
    
    coverage)
        print_status "Executando com cobertura de código..."
        pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        print_success "Relatório de cobertura: htmlcov/index.html"
        ;;
    
    payments)
        print_status "Testes de pagamentos parciais..."
        pytest tests/test_installment_payments.py -v
        ;;
    
    balances)
        print_status "Testes de saldos..."
        pytest tests/test_installment_list_balances.py -v
        ;;
    
    debt)
        print_status "Testes de débito de clientes..."
        pytest tests/test_customer_total_debt.py -v
        ;;
    
    reports)
        print_status "Testes de relatórios..."
        pytest tests/test_reports_corrections.py -v
        ;;
    
    cron)
        print_status "Testes de cron jobs..."
        pytest tests/test_cron_jobs.py -v
        ;;
    
    watch)
        print_status "Modo watch (Ctrl+C para parar)..."
        if ! command -v ptw &> /dev/null; then
            print_warning "pytest-watch não instalado. Instalando..."
            pip install pytest-watch
        fi
        ptw tests/ -- -v
        ;;
    
    debug)
        print_status "Modo debug (printa tudo)..."
        pytest tests/ -v -s --tb=long
        ;;
    
    *)
        echo "Uso: $0 [opção]"
        echo ""
        echo "Opções:"
        echo "  all         - Executar todos os testes (padrão)"
        echo "  fast        - Testes rápidos (sem cobertura)"
        echo "  coverage    - Com relatório de cobertura"
        echo "  payments    - Apenas testes de pagamentos"
        echo "  balances    - Apenas testes de saldos"
        echo "  debt        - Apenas testes de débito"
        echo "  reports     - Apenas testes de relatórios"
        echo "  cron        - Apenas testes de cron jobs"
        echo "  watch       - Modo watch (reexecutar ao salvar)"
        echo "  debug       - Modo debug com output completo"
        echo ""
        echo "Exemplos:"
        echo "  ./scripts/run_tests.sh all"
        echo "  ./scripts/run_tests.sh coverage"
        echo "  ./scripts/run_tests.sh payments -v"
        exit 1
        ;;
esac

echo ""
print_success "Testes completados!"
