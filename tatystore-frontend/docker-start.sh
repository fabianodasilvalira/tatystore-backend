#!/bin/bash

# Script de inicialização rápida para TatyStore com Docker
# Este script facilita a configuração inicial do projeto

echo "🚀 Iniciando configuração do TatyStore com Docker..."
echo ""

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    echo "   Visite: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verifica se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    echo "   Visite: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker e Docker Compose estão instalados"
echo ""

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env a partir do .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua GEMINI_API_KEY"
    echo ""
    read -p "Pressione Enter para continuar após configurar o .env..."
else
    echo "✅ Arquivo .env já existe"
fi

echo ""
echo "Escolha o modo de execução:"
echo "1) Desenvolvimento (hot-reload, porta 3000)"
echo "2) Produção (Nginx, porta 80)"
echo ""
read -p "Digite sua escolha (1 ou 2): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Iniciando modo DESENVOLVIMENTO..."
        echo "   Acesse a aplicação em: http://localhost:3000"
        echo ""
        docker-compose up tatystore-dev
        ;;
    2)
        echo ""
        echo "🏭 Iniciando modo PRODUÇÃO..."
        echo "   Acesse a aplicação em: http://localhost"
        echo ""
        docker-compose up tatystore-prod
        ;;
    *)
        echo "❌ Opção inválida. Execute o script novamente."
        exit 1
        ;;
esac
