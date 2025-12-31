#!/bin/sh

echo "Iniciando TatyStore API..."

# Aguardar o banco de dados estar pronto
echo "Aguardando banco de dados..."
until nc -z db 5432; do
  echo "Banco de dados não está pronto - aguardando..."
  sleep 2
done
echo "Banco de dados pronto!"

# Criar cliente padrão "Venda na Loja" para todas as empresas
echo "Verificando/criando cliente padrão 'Venda na Loja'..."
python scripts/create_default_customer_sql.py || echo "Aviso: Não foi possível criar cliente padrão (pode já existir)"

# Se a variável PORT existir (Render), use ela; senão use 8080 (local)
PORT=${PORT:-8080}

echo "Iniciando servidor na porta $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
