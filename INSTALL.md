# Instalação
1. Requisitos: Docker + Docker Compose
2. `cp .env.example .env` e ajuste SMTP/S3 se necessário
3. `docker compose up -d --build`
4. Postgres e MinIO sobem automaticamente; API roda migração Alembic e cria admin.
