# 📋 SISTEMA DE PERMISSÕES E PERFIS

## 📊 Tabela Completa de Permissões por Perfil

| Permissão | Descrição | Administrador | Gerente | Vendedor |
|-----------|-----------|:-------------:|:-------:|:--------:|
| **products.view** | Visualizar produtos | ✅ | ✅ | ✅ |
| **products.create** | Cadastrar novos produtos | ✅ | ✅ | ❌ |
| **products.update** | Editar informações de produtos | ✅ | ✅ | ❌ |
| **products.update_stock** | Alterar estoque de produtos | ✅ | ✅ | ❌ |
| **customers.view** | Visualizar clientes | ✅ | ✅ | ✅ |
| **customers.create** | Cadastrar novos clientes | ✅ | ✅ | ✅ |
| **customers.update** | Editar dados de clientes | ✅ | ✅ | ❌ |
| **sales.create** | Registrar vendas | ✅ | ✅ | ✅ |
| **sales.cancel** | Cancelar vendas | ✅ | ✅ | ❌ |
| **reports.view** | Visualizar relatórios | ✅ | ✅ | ❌ |
| **companies.create** | Criar novas empresas no sistema | ✅ | ❌ | ❌ |

## 🎯 Resumo por Perfil

### 👨‍💼 Administrador
**Permissões:** 10/10 (100%) + Criar Empresas

Acesso total ao sistema com todas as permissões:
- ✅ Gerenciar produtos (criar, editar, atualizar estoque)
- ✅ Gerenciar clientes (criar, editar, visualizar)
- ✅ Realizar e cancelar vendas
- ✅ Visualizar todos os relatórios
- ✅ Gerenciar usuários e configurações da empresa
- ✅ **CRIAR NOVAS EMPRESAS** (único perfil com esta permissão)

**Credenciais de Teste:**
\`\`\`
Taty: admin@taty.com / admin123
Carol: admin@carol.com / admin123
\`\`\`

---

### 👔 Gerente
**Permissões:** 10/10 (100%) **DENTRO DA EMPRESA**

**PODE FAZER TUDO** dentro da sua empresa (gestão completa):
- ✅ Visualizar, criar e editar produtos
- ✅ **Atualizar estoque de produtos**
- ✅ Gerenciar clientes (criar, editar, visualizar)
- ✅ Realizar vendas
- ✅ **Cancelar vendas**
- ✅ Visualizar relatórios gerenciais
- ❌ **NÃO PODE** criar novas empresas no sistema (apenas Admin)

**Diferença para Admin:** Gerente tem poder total na sua empresa, mas não pode criar outras empresas.

**Credenciais de Teste:**
\`\`\`
Taty: gerente@taty.com / gerente123
Carol: gerente@carol.com / gerente123
\`\`\`

---

### 🛒 Vendedor
**Permissões:** 4/10 (40%)

Permissões básicas para operação de vendas:
- ✅ Visualizar produtos
- ✅ Visualizar e cadastrar clientes
- ✅ Realizar vendas
- ❌ **NÃO PODE** criar ou editar produtos
- ❌ **NÃO PODE** alterar estoque
- ❌ **NÃO PODE** editar dados de clientes
- ❌ **NÃO PODE** cancelar vendas
- ❌ **NÃO PODE** visualizar relatórios

**Credenciais de Teste:**
\`\`\`
Taty: vendedor@taty.com / vendedor123
Carol: vendedor@carol.com / vendedor123
\`\`\`

---

## 🔒 Isolamento Multi-Tenant

**IMPORTANTE:** Todas as permissões respeitam o isolamento por empresa:

- ✅ Usuários **APENAS** acessam dados da própria empresa
- ✅ Admin da Taty **NÃO** acessa dados da Carol
- ✅ Gerente da Carol **NÃO** acessa dados da Taty
- ✅ Token JWT inclui `company_id` para validação
- ✅ Todas as queries filtram automaticamente por `company_id`

### Exemplo de Isolamento:
\`\`\`json
// Token JWT de admin@taty.com
{
  "sub": "user_uuid",
  "email": "admin@taty.com",
  "company_id": 1,
  "company_slug": "taty",
  "role": "Administrador"
}
\`\`\`

Este token **APENAS** acessa dados onde `company_id = 1`

---

## 📝 Como Funciona o Controle de Acesso

### 1. Autenticação (Login)
\`\`\`python
POST /api/v1/auth/login-json
{
  "email": "vendedor@taty.com",
  "password": "vendedor123"
}
\`\`\`

**Validações:**
- ✅ Email e senha corretos
- ✅ Usuário ativo (`is_active = true`)
- ✅ Empresa ativa (`company.is_active = true`)
- ✅ Gera token JWT com `company_id` e `role`

### 2. Autorização (Permissões)
\`\`\`python
# Exemplo: Endpoint protegido
@router.post("/products")
async def create_product(
    current_user: User = Depends(get_current_user)
):
    # Valida permissão
    if not has_permission(current_user, "products.create"):
        raise HTTPException(403, "Sem permissão")
    
    # Valida company_id automaticamente
    # Token company_id == 1 → só acessa dados de company_id = 1
\`\`\`

### 3. Validação de Empresa
\`\`\`python
# Todas as queries incluem filtro automático
products = db.query(Product).filter(
    Product.company_id == current_user.company_id
).all()
\`\`\`

---

## 🧪 Testando Permissões

### Teste 1: Login como Vendedor
\`\`\`bash
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
     -H "Content-Type: application/json" \
     -d '{"email": "vendedor@taty.com", "password": "vendedor123"}'
\`\`\`

**Resultado:**
\`\`\`json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "email": "vendedor@taty.com",
    "role": "Vendedor",
    "company_slug": "taty"
  }
}
\`\`\`

### Teste 2: Tentar Criar Produto como Vendedor (deve falhar)
\`\`\`bash
curl -X POST "http://localhost:8000/api/v1/products" \
     -H "Authorization: Bearer eyJ..." \
     -H "Content-Type: application/json" \
     -d '{"name": "Teste", "sale_price": 10}'
\`\`\`

**Resultado esperado:**
\`\`\`json
{
  "detail": "Acesso negado. Perfil requerido: Administrador, Gerente"
}
\`\`\`

### Teste 3: Login como Gerente e Cancelar Venda (deve funcionar)
\`\`\`bash
# 1. Login como gerente
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
     -H "Content-Type: application/json" \
     -d '{"email": "gerente@taty.com", "password": "gerente123"}'

# 2. Cancelar venda (agora funciona!)
curl -X POST "http://localhost:8000/api/v1/sales/123/cancel" \
     -H "Authorization: Bearer eyJ..."
\`\`\`

**Resultado esperado:**
\`\`\`json
{
  "id": "123",
  "status": "CANCELLED",
  "message": "Venda cancelada com sucesso"
}
\`\`\`

### Teste 4: Tentar Criar Empresa como Gerente (deve falhar)
\`\`\`bash
curl -X POST "http://localhost:8000/api/v1/companies" \
     -H "Authorization: Bearer eyJ..." \
     -H "Content-Type: application/json" \
     -d '{"name": "Nova Empresa", "slug": "nova", ...}'
\`\`\`

**Resultado esperado:**
\`\`\`json
{
  "detail": "Acesso negado. Perfil requerido: Administrador"
}
\`\`\`

---

## 🔍 Endpoints Úteis

### Listar Credenciais de Teste
\`\`\`bash
GET /api/v1/public/test-credentials
\`\`\`

Retorna todas as credenciais disponíveis para testes.

### Documentação Interativa (Swagger)
\`\`\`
GET /docs
\`\`\`

**Como usar o Swagger:**
1. Acesse `/docs`
2. Faça login via `POST /api/v1/auth/login-json`
3. Copie o `access_token` da resposta
4. Clique no botão **"Authorize"** no topo
5. Cole **APENAS o token** (sem "Bearer")
6. Clique em "Authorize"
7. Pronto! Agora você pode testar todos os endpoints

---

## 📊 Estatísticas do Sistema

**Dados de Teste Criados Automaticamente:**

| Item | Quantidade | Detalhes |
|------|------------|----------|
| Empresas | 2 | Taty e Carol |
| Usuários | 8 | 4 por empresa (Admin, Gerente, 2 Vendedores) |
| Produtos | 24 | 12 por empresa (10 ativos, 2 inativos) |
| Clientes | 8 | 4 por empresa (3 ativos, 1 inativo) |
| Vendas | ~44 | ~22 por empresa (3 meses de histórico) |
| Parcelas | ~100 | Estados variados (pagas, pendentes, vencidas) |
| Permissões | 10 | Sistema completo de controle de acesso |
| Roles | 3 | Administrador, Gerente, Vendedor |

---

## 🚀 Cenários de Teste Cobertos

✅ Login multi-tenant (3 perfis por empresa)  
✅ Isolamento completo entre empresas  
✅ Produtos com baixo estoque (alertas)  
✅ Produtos e clientes inativos  
✅ Usuários inativos (bloqueio de login)  
✅ Vendas canceladas (restauração de estoque)  
✅ Crediário com parcelas vencidas  
✅ Relatórios de vendas, lucro, inadimplência  
✅ Histórico temporal de 3 meses  
✅ Controle de permissões granular  
✅ Validação de estoque em vendas  
✅ Cálculo automático de parcelas  

---

## ⚠️ Observações Importantes

1. **Hierarquia de Perfis:**
   - **Admin:** Cria empresas + Gestão completa de qualquer empresa
   - **Gerente:** Gestão completa da sua empresa (não cria outras empresas)
   - **Vendedor:** Apenas vendas e consultas básicas

2. **Usuários Inativos:** Não podem fazer login em hipótese alguma

3. **Empresas Inativas:** Bloqueiam login de todos os usuários

4. **Produtos Inativos:** Não aparecem em vendas mas mantêm histórico

5. **Clientes Inativos:** Não podem realizar novas compras

6. **Isolamento Absoluto:** Empresa A nunca acessa dados da Empresa B

7. **Tokens Temporários:** Access tokens expiram (configure em `settings`)

8. **Senhas Seguras:** Sistema exige senhas fortes (8+ chars, maiúsculas, números)

---

## 📞 Suporte

Para dúvidas sobre permissões ou acesso:
1. Verifique o perfil do usuário no sistema
2. Consulte a tabela de permissões acima
3. Teste com as credenciais fornecidas
4. Acesse `/docs` para documentação completa

**Sistema desenvolvido com isolamento multi-tenant completo e seguro!**
