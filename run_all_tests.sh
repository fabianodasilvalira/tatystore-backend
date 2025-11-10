#!/bin/bash

# Script para executar todos os testes com relatório detalhado

echo "================================"
echo "TatyStore Backend - Suite de Testes"
echo "================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest não está instalado${NC}"
    echo "Instale com: pip install pytest"
    exit 1
fi

# Verificar se slowapi está instalado
if ! python -c "import slowapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  slowapi não está instalado${NC}"
    echo "Instalando slowapi..."
    pip install slowapi
fi

echo -e "${YELLOW}📋 Executando suite completa de testes...${NC}"
echo ""

# Executar todos os testes com verbose
pytest tests/ -v --tb=short --color=yes

# Capturar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Todos os testes passaram!${NC}"
    echo ""
    echo "Resumo:"
    pytest tests/ --collect-only -q | tail -1
    exit 0
else
    echo ""
    echo -e "${RED}❌ Alguns testes falharam${NC}"
    exit 1
fi
