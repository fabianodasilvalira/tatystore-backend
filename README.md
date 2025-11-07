# Taty Store API (FastAPI) — Multi-tenant por caminho
- Isolamento por empresa via `/{company_slug}/api/v1/...`
- Se usuário tenta outra empresa → **404 Not Found**
- RBAC com roles/permissions (Administrador, Vendedor, etc.)
- Rate limit **por empresa** (SlowAPI)
- Auditoria em banco + alertas por e-mail
- Uploads por empresa:
  - `uploads/<slug>/products/`
  - `uploads/<slug>/customers/`
## Rodar
```bash
cp .env.example .env
docker compose up -d --build
```
Docs: http://localhost:8000/taty/api/v1/docs
Admin inicial (empresa `taty`): `admin@local` / `admin@2025`



## Relatórios (Avançado)
Endpoints:
- `/{company_slug}/api/v1/reports/dash/overview`
- `/{company_slug}/api/v1/reports/dash/sales-by-day?days=30`
- `/{company_slug}/api/v1/reports/dash/top-products?limit=5`
- `/{company_slug}/api/v1/reports/dash/payment-method-share`
- `/{company_slug}/api/v1/reports/dash/overdue-customers`
- `/{company_slug}/api/v1/reports/dash/low-stock?threshold=5`
