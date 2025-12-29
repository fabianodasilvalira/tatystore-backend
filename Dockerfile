FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        netcat-openbsd \
        postgresql-client \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Adicionado --root-user-action=ignore para evitar o erro de permissão no log
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN chmod +x /app/entrypoint.sh

# Mantendo 8080 para alinhar com seu domínio no Dokploy
EXPOSE 8080

CMD ["/app/entrypoint.sh"]