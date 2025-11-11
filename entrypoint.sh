#!/bin/sh

echo "Iniciando TatyStore API..."

# Se a variável PORT existir (Render), use ela; senão use 8080 (local)
PORT=${PORT:-8080}

exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
