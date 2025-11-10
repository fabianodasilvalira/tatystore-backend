#!/bin/bash
set -e

echo "TatyStore API - Iniciando..."
echo "===================================="

# Wait for database
echo "Aguardando o banco de dados..."
max_attempts=30
attempt=0
while ! nc -z db 5432; do
  attempt=$((attempt+1))
  if [ $attempt -ge $max_attempts ]; then
    echo "❌ Timeout aguardando banco de dados"
    exit 1
  fi
  echo "  Tentativa $attempt/$max_attempts..."
  sleep 2
done

echo "✓ Banco de dados disponível!"

echo ""
echo "===================================="
echo "Iniciando servidor FastAPI..."
echo "===================================="

set +e

# Start the API - migrações serão executadas na startup do FastAPI
# O uvicorn irá chamar init_db() que tenta alembic com fallback para SQLAlchemy
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
