# Como Resolver o Erro: column products.brand does not exist

## Problema
Você adicionou o campo `brand` ao modelo Product no código Python, mas a coluna não existe no banco de dados PostgreSQL.

## Solução Rápida (Recomendada)

### Opção 1: Executar o Script SQL Diretamente
Execute o script `scripts/add_brand_column.sql` que criamos:

\`\`\`bash
# Dentro do container do backend
docker exec -it tatystore-backend-api python -c "
from app.core.database import engine
with open('scripts/add_brand_column.sql', 'r') as f:
    sql = f.read()
with engine.connect() as conn:
    conn.execute(sql)
    conn.commit()
"
\`\`\`

### Opção 2: Conectar diretamente ao PostgreSQL
\`\`\`bash
# Conectar ao banco de dados
docker exec -it tatystore-backend-db psql -U postgres -d tatystore

# Executar os comandos:
ALTER TABLE products ADD COLUMN brand VARCHAR(100);
ALTER TABLE products ADD COLUMN image_url VARCHAR(500);

# Verificar:
\d products
\`\`\`

### Opção 3: Usar Alembic (Recomendado para produção)
\`\`\`bash
# Dentro do container do backend
docker exec -it tatystore-backend-api alembic upgrade head
\`\`\`

## Verificação
Após executar qualquer uma das opções, reinicie o container da API:

\`\`\`bash
docker restart tatystore-backend-api
\`\`\`

Teste a API:
\`\`\`bash
curl http://localhost:8000/api/v1/products/?skip=0&limit=10&active_only=true
\`\`\`

## Por que isso aconteceu?
1. Você modificou o modelo Python (`app/models/product.py`) adicionando o campo `brand`
2. A migração Alembic existe (`002_add_product_brand_and_image.py`)
3. Mas a migração não foi executada no banco de dados
4. SQLAlchemy tenta buscar a coluna que não existe fisicamente

## Prevenção Futura
Sempre que adicionar/modificar campos no modelo:

1. **Criar migração**:
   \`\`\`bash
   docker exec -it tatystore-backend-api alembic revision --autogenerate -m "descrição"
   \`\`\`

2. **Aplicar migração**:
   \`\`\`bash
   docker exec -it tatystore-backend-api alembic upgrade head
   \`\`\`

3. **Verificar no banco**:
   \`\`\`bash
   docker exec -it tatystore-backend-db psql -U postgres -d tatystore -c "\d products"
