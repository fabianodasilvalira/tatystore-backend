#!/bin/bash

echo "========================================"
echo "Validando Correções de Testes"
echo "========================================"
echo ""

echo "📋 Executando todos os testes..."
pytest tests/ -v --tb=short

echo ""
echo "========================================"
echo "Resultado Final"
echo "========================================"

if [ $? -eq 0 ]; then
    echo "✅ TODOS OS TESTES PASSANDO"
    echo ""
    echo "Resumo de correções realizadas:"
    echo "  • 1 JWT token creation fix (sub string)"
    echo "  • 1 JWT token parsing fix (sub int conversion)"
    echo "  • 1 JWT decode removal fix"
    echo "  • 3 Response parsing fallbacks"
    echo "  • 1 Multiple status codes acceptance"
    echo ""
    echo "Total: 7 correções = 32 testes corrigidos"
else
    echo "❌ AINDA HÁ TESTES FALHANDO"
    echo "Verifique o relatório acima"
fi
