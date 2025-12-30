# 🚀 Guia Visual: Configurar Frontend no Dokploy

## 📋 Arquitetura Final

```
Frontend:  https://app.tatystore.cloud  (React + Nginx)
Backend:   https://tatystore.cloud/api  (FastAPI)
Docs:      https://tatystore.cloud/docs (Swagger)
```

---

## 🔧 PASSO 1: Criar Novo Projeto no Dokploy

1. No painel do Dokploy, clique em **"New Project"** ou **"Create Application"**
2. Escolha o tipo: **"Docker Compose"**
3. Nome do projeto: `tatystore-frontend`
4. Clique em **"Create"**

---

## 📦 PASSO 2: Fazer Upload dos Arquivos

### **Opção A: Upload Manual (Mais Simples)**

1. Compacte a pasta `tatystore-frontend` em um arquivo `.zip`
2. No Dokploy, vá em **"Source"** ou **"Files"**
3. Faça upload do arquivo `.zip`
4. Certifique-se de que estes arquivos estão incluídos:
   - ✅ `Dockerfile`
   - ✅ `docker-compose.yml`
   - ✅ `nginx.conf`
   - ✅ `package.json`
   - ✅ Todo o código fonte

### **Opção B: Conectar Repositório Git**

1. No Dokploy, vá em **"Source"**
2. Conecte seu repositório Git
3. Selecione a branch: `main` ou `master`
4. Defina o caminho: `/tatystore-frontend`

---

## ⚙️ PASSO 3: Configurar Variáveis de Ambiente

No Dokploy, vá em **"Environment"** ou **"Environment Variables"** e adicione:

```env
GEMINI_API_KEY=sua_chave_api_aqui
VITE_API_URL=https://tatystore.cloud
NODE_ENV=production
PORT=80
```

> ⚠️ **IMPORTANTE**: Obtenha sua `GEMINI_API_KEY` em: https://aistudio.google.com/app/apikey

**Como adicionar:**
1. Clique em **"Add Variable"**
2. Nome: `GEMINI_API_KEY`
3. Valor: Cole sua chave da API
4. Repita para as outras variáveis
5. Clique em **"Save"**

---

## 🌐 PASSO 4: Configurar Domínio (IMPORTANTE!)

No Dokploy, vá em **"Domains"** ou **"Domain"** e configure:

### **Configuração do Frontend:**

| Campo | Valor |
|-------|-------|
| **Host** | `app.tatystore.cloud` |
| **Path** | `/` (ou deixe vazio) |
| **Internal Path** | `/` (ou deixe vazio) |
| **Container Port** | `80` |
| **HTTPS** | ✅ **ATIVADO** |
| **Certificate Provider** | Let's Encrypt |

**Exemplo visual:**
```
┌─────────────────────────────────────┐
│ Host:           app.tatystore.cloud │
│ Path:           /                   │
│ Internal Path:  /                   │
│ Container Port: 80                  │
│ HTTPS:          ✅ ON               │
└─────────────────────────────────────┘
```

---

## 🔧 PASSO 5: Configurar DNS na Hostinger

**MUITO IMPORTANTE**: Você precisa criar um registro DNS para `app.tatystore.cloud`

1. Acesse o painel da **Hostinger**
2. Vá em **"DNS / Name Servers"** ou **"Gerenciar DNS"**
3. Adicione um novo registro:

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| **A** | `app` | `IP do servidor Dokploy` | 3600 |

**OU** (se o Dokploy fornecer um CNAME):

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| **CNAME** | `app` | `dokploy.seuservidor.com` | 3600 |

> 💡 **Dica**: O IP do servidor ou CNAME você encontra no painel do Dokploy

4. Clique em **"Salvar"**
5. Aguarde a propagação DNS (pode levar de 5 minutos a 24 horas)

---

## 🏗️ PASSO 6: Configurar Build

No Dokploy, vá em **"Build Settings"** ou **"Deploy"**:

| Configuração | Valor |
|--------------|-------|
| **Build Command** | `docker-compose build` |
| **Dockerfile** | `Dockerfile` |
| **Docker Compose File** | `docker-compose.yml` |
| **Build Context** | `.` (raiz do projeto) |

---

## 🚀 PASSO 7: Fazer Deploy

1. Clique em **"Deploy"** ou **"Build & Deploy"**
2. Aguarde o build completar (2-5 minutos)
3. Monitore os logs para verificar se há erros

**Logs esperados:**
```
✓ Building image...
✓ Copying files...
✓ Running npm install...
✓ Running npm run build...
✓ Creating Nginx container...
✓ Container started successfully
✓ Health check: healthy
```

---

## 🔐 PASSO 8: Configurar CORS no Backend

**MUITO IMPORTANTE**: O backend precisa permitir requisições do frontend!

1. No Dokploy, vá no projeto do **backend** (`tatystore-backend`)
2. Vá em **"Environment Variables"**
3. Adicione ou atualize a variável:

```env
BACKEND_CORS_ORIGINS=https://app.tatystore.cloud,https://tatystore.cloud
```

4. Clique em **"Save"**
5. Faça **"Redeploy"** do backend

---

## ✅ PASSO 9: Verificar se Está Funcionando

### **1. Verificar Status do Container**

No Dokploy, verifique:
- ✅ Status: **Running** (verde)
- ✅ Health Check: **Healthy**
- ✅ Logs sem erros críticos

### **2. Testar o Acesso**

Abra o navegador e acesse:
```
https://app.tatystore.cloud
```

Você deve ver a interface do TatyStore carregando!

### **3. Verificar Comunicação com Backend**

1. Abra o **DevTools** (F12)
2. Vá na aba **Network**
3. Faça uma ação que chame o backend
4. Verifique se as requisições para `https://tatystore.cloud/api` estão funcionando
5. **NÃO** deve aparecer erro de CORS

---

## 🎉 Arquitetura Final

```
┌─────────────────────────────────────────────┐
│         TATYSTORE - ARQUITETURA             │
├─────────────────────────────────────────────┤
│                                             │
│  🌐 Frontend (React + Nginx)                │
│     https://app.tatystore.cloud             │
│     ├─ /                                    │
│     ├─ /produtos                            │
│     └─ /carrinho                            │
│                                             │
│  🔧 Backend (FastAPI)                       │
│     https://tatystore.cloud                 │
│     ├─ /api → Endpoints da API              │
│     └─ /docs → Documentação Swagger         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔍 Troubleshooting

### **Problema 1: "DNS_PROBE_FINISHED_NXDOMAIN"**

**Causa**: DNS não foi configurado ou ainda não propagou

**Solução**:
1. Verifique se adicionou o registro DNS na Hostinger
2. Aguarde a propagação (pode levar até 24h)
3. Teste com: `nslookup app.tatystore.cloud`

### **Problema 2: Certificado SSL não funciona**

**Causa**: Let's Encrypt não conseguiu gerar o certificado

**Solução**:
1. Certifique-se de que o DNS está apontando corretamente
2. Aguarde alguns minutos e tente novamente
3. Verifique os logs do Dokploy

### **Problema 3: CORS Error**

**Causa**: Backend não está permitindo requisições do frontend

**Solução**:
1. Verifique se `BACKEND_CORS_ORIGINS` está configurado no backend
2. Certifique-se de que inclui `https://app.tatystore.cloud`
3. Faça redeploy do backend

### **Problema 4: Página em branco**

**Causa**: Variável `VITE_API_URL` não configurada

**Solução**:
1. Verifique as variáveis de ambiente no Dokploy
2. Certifique-se de que `VITE_API_URL=https://tatystore.cloud` está definida
3. Faça redeploy do frontend

---

## 📝 Checklist Final

Antes de considerar concluído, verifique:

### **Frontend**
- [ ] Projeto criado no Dokploy
- [ ] Arquivos enviados (zip ou Git)
- [ ] Variáveis de ambiente configuradas
- [ ] Domínio `app.tatystore.cloud` configurado
- [ ] DNS configurado na Hostinger
- [ ] SSL/HTTPS ativado
- [ ] Deploy realizado com sucesso
- [ ] Status: Running e Healthy

### **Backend**
- [ ] `BACKEND_CORS_ORIGINS` atualizado
- [ ] Inclui `https://app.tatystore.cloud`
- [ ] Redeploy realizado

### **Testes**
- [ ] Frontend abre em `https://app.tatystore.cloud`
- [ ] Backend responde em `https://tatystore.cloud/docs`
- [ ] Sem erros de CORS no console
- [ ] Funcionalidades que chamam API funcionam

---

## 🎯 Resumo das Configurações

### **Frontend (Dokploy)**
```
Nome: tatystore-frontend
Tipo: Docker Compose
Domínio: app.tatystore.cloud
Porta: 80
HTTPS: ✅ Ativado
```

**Variáveis de Ambiente:**
```env
GEMINI_API_KEY=sua_chave_api_aqui
VITE_API_URL=https://tatystore.cloud
NODE_ENV=production
PORT=80
```

### **Backend (Dokploy)**
```
Nome: tatystore-backend
Domínio: tatystore.cloud
Path: /
Porta: 8080
HTTPS: ✅ Ativado
```

**Variável de Ambiente Adicional:**
```env
BACKEND_CORS_ORIGINS=https://app.tatystore.cloud,https://tatystore.cloud
```

### **DNS (Hostinger)**
```
Tipo: A (ou CNAME)
Nome: app
Valor: IP do servidor (ou CNAME do Dokploy)
TTL: 3600
```

---

**Tempo estimado total**: 15-20 minutos  
**Última atualização**: 29/12/2025  
**Status**: ✅ Pronto para uso
