#!/bin/bash

# Script rápido para rodar testes específicos de pagamentos parciais
# Uso: ./scripts/run_tests_quick.sh [opção]

set -e

echo "======================================"
echo "  Testes de Pagamentos Parciais"
echo "======================================"

case "${1:-all}" in
  all)
    echo "Rodando TODOS os testes de pagamentos parciais..."
    pytest tests/test_partial_payments_complete.py -v
    ;;
  
  metade)
    echo "Rodando testes de pagamento PELA METADE..."
    pytest tests/test_partial_payments_complete.py::test_pay_installment_half -v
    ;;
  
  qualquer)
    echo "Rodando testes de pagamento por QUALQUER VALOR..."
    pytest tests/test_partial_payments_complete.py -k "any_amount or various" -v
    ;;
  
  multiplos)
    echo "Rodando testes de MÚLTIPLOS PAGAMENTOS..."
    pytest tests/test_partial_payments_complete.py -k "multiple" -v
    ;;
  
  validacoes)
    echo "Rodando testes de VALIDAÇÕES..."
    pytest tests/test_partial_payments_complete.py -k "validation or exceed" -v
    ;;
  
  rotas)
    echo "Rodando testes de ROTAS com saldos..."
    pytest tests/test_partial_payments_complete.py -k "list or filter" -v
    ;;
  
  coverage)
    echo "Rodando com COBERTURA DE CÓDIGO..."
    pytest --cov=. --cov-report=term-missing --cov-report=html tests/test_partial_payments_complete.py
    echo ""
    echo "Relatório HTML gerado em: htmlcov/index.html"
    ;;
  
  *)
    echo "Uso: $0 [opção]"
    echo ""
    echo "Opções disponíveis:"
    echo "  all        - Roda todos os testes (padrão)"
    echo "  metade     - Testa pagamentos pela metade"
    echo "  qualquer   - Testa pagamentos por qualquer valor"
    echo "  multiplos  - Testa múltiplos pagamentos"
    echo "  validacoes - Testa validações e restrições"
    echo "  rotas      - Testa rotas de listagem com saldos"
    echo "  coverage   - Roda com análise de cobertura"
    exit 1
    ;;
esac

echo ""
echo "======================================"
echo "  Testes finalizados!"
echo "======================================"
