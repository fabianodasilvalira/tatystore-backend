# Taty Store API (FastAPI)
- Autenticação JWT + RBAC (Administrador, Vendedor)
- Admin auto: admin@local / admin@2025
- Recuperação de senha (email) + templates
- Anti-brute-force + alerta de segurança + captcha inteligente
- Auditoria de requisições
- Produtos, Clientes, Vendas, Itens, Parcelas
- MinIO (S3) para uploads
- Jobs: parcelas vencidas + refresh de materialized views
- Relatórios otimizados (materialized view)

## Rodar
```
cp .env.example .env
docker compose up -d --build
# docs: http://localhost:8000/docs
# minio: http://localhost:9001  (minio / minio123)
```
# tatystore-backend
