#!/bin/sh

# Definir host e porta do banco (padrão: db:5432)
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}

# Tentar extrair host da DATABASE_URL se definida (simples fallback)
if [ -n "$DATABASE_URL" ]; then
    # Tenta extrair host usando regex simples (atenção: pode falhar em URLs complexas)
    # Formato esperado: postgres://user:pass@HOST:PORT/db
    CLEAN_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
    if [ -n "$CLEAN_HOST" ]; then
        DB_HOST=$CLEAN_HOST
    fi
fi

echo "Iniciando TatyStore API..."
echo "Ambiente: Host DB=$DB_HOST, Porta=$DB_PORT"

# Aguardar o banco de dados estar pronto
echo "Aguardando banco de dados em $DB_HOST:$DB_PORT..."
until nc -z $DB_HOST $DB_PORT; do
  echo "Banco de dados ($DB_HOST:$DB_PORT) não está pronto - aguardando..."
  sleep 2
done
echo "Banco de dados conectado com sucesso!"

# Criar cliente padrão "Venda na Loja" para todas as empresas
echo "Verificando/criando cliente padrão 'Venda na Loja'..."
python scripts/create_default_customer_sql.py || echo "Aviso: Não foi possível criar cliente padrão (pode já existir)"

# Se a variável PORT existir (Render), use ela; senão use 8080 (local)
PORT=${PORT:-8080}

echo "Iniciando servidor na porta $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
