# 🚀 Configuração do Frontend TatyStore no Dokploy

## 📋 Situação Atual

✅ **Backend**: Funcionando em `https://tatystore.cloud/docs`  
⚠️ **Frontend**: Precisa ser configurado no Dokploy

---

## 🎯 Objetivo

Configurar o frontend para acessar através do domínio `tatystore.cloud` (ou subdomínio como `app.tatystore.cloud`)

---

## 📦 Opções de Configuração

### **Opção 1: Frontend no Domínio Principal** (Recomendado)
- Frontend: `https://tatystore.cloud`
- Backend API: `https://tatystore.cloud/api`
- Docs: `https://tatystore.cloud/docs`

### **Opção 2: Frontend em Subdomínio**
- Frontend: `https://app.tatystore.cloud`
- Backend API: `https://tatystore.cloud/api`
- Docs: `https://tatystore.cloud/docs`

---

## 🔧 Passo a Passo - Configuração no Dokploy

### **1️⃣ Criar Novo Projeto no Dokploy**

1. Acesse o painel do Dokploy na Hostinger
2. Clique em **"Create Project"** ou **"New Application"**
3. Escolha **"Docker Compose"** como tipo de deploy
4. Dê um nome: `tatystore-frontend`

---

### **2️⃣ Configurar o Repositório**

**Se estiver usando Git:**
1. Conecte seu repositório Git
2. Selecione a branch: `main` ou `master`
3. Defina o caminho: `/tatystore-frontend`

**Se estiver fazendo upload manual:**
1. Faça upload da pasta `tatystore-frontend` completa
2. Certifique-se de incluir:
   - `Dockerfile`
   - `docker-compose.yml`
   - `nginx.conf`
   - Todo o código fonte

---

### **3️⃣ Configurar Variáveis de Ambiente**

No painel do Dokploy, vá em **Environment Variables** e adicione:

```env
# OBRIGATÓRIA - Sua chave da API Gemini
GEMINI_API_KEY=sua_chave_api_aqui

# URL do Backend (já configurado)
VITE_API_URL=https://tatystore.cloud

# Ambiente de produção
NODE_ENV=production

# Porta (padrão)
PORT=80
```

> ⚠️ **IMPORTANTE**: A variável `GEMINI_API_KEY` é obrigatória para o funcionamento da aplicação!

---

### **4️⃣ Configurar o Domínio**

#### **Opção A: Domínio Principal (tatystore.cloud)**

1. No Dokploy, vá em **Domains** ou **Settings**
2. Adicione o domínio: `tatystore.cloud`
3. Configure o **Path Prefix** (se necessário):
   - Frontend: `/` (raiz)
   - Backend: `/api` (já configurado)
   - Docs: `/docs` (já configurado)

4. Ative **SSL/HTTPS** (Let's Encrypt)
5. Salve as configurações

#### **Opção B: Subdomínio (app.tatystore.cloud)**

1. No Dokploy, vá em **Domains**
2. Adicione o subdomínio: `app.tatystore.cloud`
3. Ative **SSL/HTTPS** (Let's Encrypt)
4. Salve as configurações

5. **Configure o DNS na Hostinger:**
   - Vá no painel de DNS da Hostinger
   - Adicione um registro **A** ou **CNAME**:
     - **Tipo**: A ou CNAME
     - **Nome**: `app`
     - **Valor**: IP do servidor ou domínio do Dokploy
     - **TTL**: 3600

---

### **5️⃣ Configurar o Build**

1. No Dokploy, vá em **Build Settings**
2. Certifique-se de que está usando:
   - **Build Command**: `docker-compose build`
   - **Dockerfile**: `Dockerfile`
   - **Docker Compose File**: `docker-compose.yml`

3. **Porta do Container**: `80`
4. **Health Check**: Ativado (já configurado no docker-compose.yml)

---

### **6️⃣ Deploy**

1. Clique em **Deploy** ou **Build & Deploy**
2. Aguarde o build completar (pode levar 2-5 minutos)
3. Monitore os logs para verificar se há erros

---

## ✅ Verificação Pós-Deploy

### **1. Verificar se o Container está Rodando**

No Dokploy, verifique:
- ✅ Status: **Running** (verde)
- ✅ Health Check: **Healthy**
- ✅ Logs sem erros críticos

### **2. Testar o Acesso**

Abra o navegador e acesse:
- `https://tatystore.cloud` (ou `https://app.tatystore.cloud`)

Você deve ver a interface do TatyStore carregando.

### **3. Verificar Comunicação com o Backend**

1. Abra o **DevTools** do navegador (F12)
2. Vá na aba **Network**
3. Faça uma ação que chame o backend
4. Verifique se as requisições para `https://tatystore.cloud/api` estão funcionando

---

## 🔍 Troubleshooting

### **Problema 1: "Cannot GET /"**

**Causa**: Nginx não está servindo o index.html  
**Solução**:
1. Verifique se o arquivo `nginx.conf` foi copiado corretamente
2. Reconstrua a imagem: `docker-compose build --no-cache`

### **Problema 2: Página em branco**

**Causa**: Variável `VITE_API_URL` não configurada  
**Solução**:
1. Verifique as variáveis de ambiente no Dokploy
2. Certifique-se de que `VITE_API_URL=https://tatystore.cloud` está definida
3. Faça um novo deploy

### **Problema 3: CORS Error**

**Causa**: Backend não está permitindo requisições do frontend  
**Solução**:
1. Verifique as configurações de CORS no backend
2. Adicione o domínio do frontend nas origens permitidas:
   ```python
   # No backend (FastAPI)
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://tatystore.cloud", "https://app.tatystore.cloud"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### **Problema 4: SSL/HTTPS não funciona**

**Causa**: Certificado não foi gerado  
**Solução**:
1. No Dokploy, vá em **SSL Settings**
2. Ative **Let's Encrypt**
3. Aguarde a geração do certificado (pode levar alguns minutos)
4. Certifique-se de que o domínio está apontando corretamente para o servidor

### **Problema 5: Rotas do React Router retornam 404**

**Causa**: Nginx não está redirecionando para index.html  
**Solução**:
- Já está configurado no `nginx.conf` (linha 100: `try_files $uri $uri/ /index.html;`)
- Se ainda ocorrer, reconstrua a imagem

---

## 📊 Arquitetura Final

```
┌─────────────────────────────────────────────┐
│         https://tatystore.cloud             │
├─────────────────────────────────────────────┤
│                                             │
│  Frontend (React + Nginx)                   │
│  ├─ / → Interface do usuário                │
│  ├─ /produtos → Página de produtos          │
│  └─ /carrinho → Carrinho de compras         │
│                                             │
│  Backend (FastAPI)                          │
│  ├─ /api → Endpoints da API                 │
│  └─ /docs → Documentação Swagger            │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔐 Segurança

Seu frontend já está configurado com:
- ✅ Headers de segurança (CSP, X-Frame-Options, etc)
- ✅ Proteção contra XSS e clickjacking
- ✅ Usuário não-root no container
- ✅ Arquivos sensíveis bloqueados (.env, .git)
- ✅ HTTPS/SSL (via Let's Encrypt)
- ✅ Limites de recursos (CPU, memória)

---

## 📝 Comandos Úteis

### **Ver logs do container**
```bash
docker-compose logs -f tatystore_frontend
```

### **Reconstruir a imagem**
```bash
docker-compose build --no-cache tatystore_frontend
```

### **Testar localmente antes do deploy**
```bash
docker-compose up tatystore_frontend
```

### **Verificar health check**
```bash
docker ps
# Procure por "healthy" na coluna STATUS
```

---

## 🎉 Próximos Passos

Após o deploy bem-sucedido:

1. ✅ Teste todas as funcionalidades da aplicação
2. ✅ Verifique se as chamadas à API estão funcionando
3. ✅ Configure monitoramento (se disponível no Dokploy)
4. ✅ Configure backups automáticos
5. ✅ Adicione analytics (Google Analytics, etc)

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs no Dokploy
2. Consulte a documentação do Dokploy
3. Verifique se todas as variáveis de ambiente estão configuradas
4. Certifique-se de que o domínio está apontando corretamente

---

## 🔄 Atualizações Futuras

Para atualizar o frontend:
1. Faça as alterações no código
2. Commit e push para o repositório (se usando Git)
3. No Dokploy, clique em **Redeploy** ou **Build & Deploy**
4. Aguarde o novo build completar

---

**Última atualização**: 29/12/2025  
**Versão**: 1.0.0
