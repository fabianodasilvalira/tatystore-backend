# 🎯 Configuração Completa: Backend + Frontend no Dokploy

## 📊 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    TATYSTORE.CLOUD                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🌐 FRONTEND (React + Nginx)                            │
│     URL: https://app.tatystore.cloud                    │
│     Container: tatystore_frontend                       │
│     Porta: 80                                           │
│                                                         │
│  🔧 BACKEND (FastAPI)                                   │
│     URL: https://tatystore.cloud                        │
│     Container: tatystore_backend                        │
│     Porta: 8080                                         │
│     Rotas:                                              │
│       - /api → API REST                                 │
│       - /docs → Documentação Swagger                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ CONFIGURAÇÃO DO BACKEND (Já Feito)

### **Domínio no Dokploy:**

| Campo | Valor |
|-------|-------|
| Host | `tatystore.cloud` |
| Path | `/` |
| Internal Path | `/` |
| Container Port | `8080` |
| HTTPS | ✅ Ativado |

### **Variáveis de Ambiente:**

```env
# Adicione esta variável para permitir o frontend:
BACKEND_CORS_ORIGINS=https://app.tatystore.cloud,https://tatystore.cloud
```

> ⚠️ **IMPORTANTE**: Após adicionar `BACKEND_CORS_ORIGINS`, faça **Redeploy** do backend!

---

## 🚀 CONFIGURAÇÃO DO FRONTEND (A Fazer)

### **1. Criar Projeto no Dokploy**

1. No Dokploy, clique em **"New Project"**
2. Tipo: **"Docker Compose"**
3. Nome: `tatystore-frontend`

### **2. Upload dos Arquivos**

Envie a pasta `tatystore-frontend` (zip ou Git) com:
- ✅ `Dockerfile`
- ✅ `docker-compose.yml`
- ✅ `nginx.conf`
- ✅ Código fonte completo

### **3. Variáveis de Ambiente**

```env
GEMINI_API_KEY=sua_chave_api_aqui
VITE_API_URL=https://tatystore.cloud
NODE_ENV=production
PORT=80
```

> 🔑 Obtenha sua chave em: https://aistudio.google.com/app/apikey

### **4. Configurar Domínio**

| Campo | Valor |
|-------|-------|
| Host | `app.tatystore.cloud` |
| Path | `/` |
| Internal Path | `/` |
| Container Port | `80` |
| HTTPS | ✅ Ativado |

### **5. Configurar DNS na Hostinger**

Adicione um registro DNS:

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| A | `app` | IP do servidor Dokploy | 3600 |

> 💡 O IP do servidor você encontra no painel do Dokploy

### **6. Deploy**

1. Clique em **"Deploy"**
2. Aguarde 2-5 minutos
3. Verifique os logs

---

## 🔐 Configuração de Segurança (CORS)

### **No Backend:**

Adicione a variável de ambiente:
```env
BACKEND_CORS_ORIGINS=https://app.tatystore.cloud,https://tatystore.cloud
```

Isso permite que o frontend faça requisições para o backend sem erros de CORS.

---

## ✅ Checklist de Verificação

### **Backend**
- [x] Rodando em `https://tatystore.cloud`
- [x] Docs acessível em `https://tatystore.cloud/docs`
- [ ] `BACKEND_CORS_ORIGINS` configurado com domínio do frontend
- [ ] Redeploy realizado após adicionar CORS

### **Frontend**
- [ ] Projeto criado no Dokploy
- [ ] Arquivos enviados
- [ ] Variáveis de ambiente configuradas
- [ ] Domínio `app.tatystore.cloud` configurado
- [ ] DNS configurado na Hostinger
- [ ] SSL/HTTPS ativado
- [ ] Deploy realizado

### **Testes Finais**
- [ ] Frontend abre em `https://app.tatystore.cloud`
- [ ] Backend responde em `https://tatystore.cloud/docs`
- [ ] Sem erros de CORS no console do navegador
- [ ] Funcionalidades que chamam API funcionam

---

## 🎯 URLs Finais

Após a configuração completa:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | https://app.tatystore.cloud | Interface do usuário |
| **Backend API** | https://tatystore.cloud/api | Endpoints REST |
| **Documentação** | https://tatystore.cloud/docs | Swagger UI |
| **Health Check** | https://tatystore.cloud/health | Status do backend |

---

## 📞 Próximos Passos

1. ✅ **Backend**: Adicionar `BACKEND_CORS_ORIGINS` e fazer redeploy
2. 🚀 **Frontend**: Seguir o guia `CONFIGURACAO-DOKPLOY-VISUAL.md`
3. 🌐 **DNS**: Configurar registro `app` na Hostinger
4. ✅ **Testar**: Verificar se tudo funciona

---

**Tempo estimado**: 15-20 minutos  
**Documentação completa**: [CONFIGURACAO-DOKPLOY-VISUAL.md](file:///c:/Sistemas_Fabiano/tatyStore/tatystore-frontend/CONFIGURACAO-DOKPLOY-VISUAL.md)
