# 🚀 Guia Rápido de Deploy - TatyStore Frontend

## ✅ Pré-requisitos

- ✅ Backend rodando em `https://tatystore.cloud/docs`
- ✅ Conta no Dokploy/Hostinger
- ✅ Chave da API Gemini

---

## 📦 Passo a Passo Resumido

### **1. Criar Projeto no Dokploy**
- Tipo: **Docker Compose**
- Nome: `tatystore-frontend`

### **2. Fazer Upload dos Arquivos**
Envie a pasta `tatystore-frontend` completa, incluindo:
- ✅ `Dockerfile`
- ✅ `docker-compose.yml`
- ✅ `nginx.conf`
- ✅ Todo o código fonte

### **3. Configurar Variáveis de Ambiente**
```env
GEMINI_API_KEY=sua_chave_api_aqui
VITE_API_URL=https://tatystore.cloud
NODE_ENV=production
PORT=80
```

### **4. Configurar Domínio**

**Opção A: Domínio Principal**
- Domínio: `tatystore.cloud`
- SSL: ✅ Ativado (Let's Encrypt)

**Opção B: Subdomínio**
- Domínio: `app.tatystore.cloud`
- SSL: ✅ Ativado (Let's Encrypt)
- DNS: Adicionar registro A ou CNAME

### **5. Deploy**
- Clique em **"Deploy"** ou **"Build & Deploy"**
- Aguarde 2-5 minutos
- Verifique os logs

### **6. Testar**
- Acesse: `https://tatystore.cloud`
- Verifique se a interface carrega
- Teste as funcionalidades

---

## 📚 Documentação Completa

Para instruções detalhadas, consulte:
- 📖 [CONFIGURACAO-DOKPLOY.md](./CONFIGURACAO-DOKPLOY.md) - Guia completo
- ⚙️ [VARIAVEIS-AMBIENTE-DOKPLOY.md](./VARIAVEIS-AMBIENTE-DOKPLOY.md) - Variáveis de ambiente

---

## 🔍 Verificação Rápida

```bash
# Status do container
docker ps | grep tatystore_frontend

# Ver logs
docker-compose logs -f tatystore_frontend

# Testar health check
curl -I https://tatystore.cloud
```

---

## 🆘 Problemas Comuns

| Problema | Solução |
|----------|---------|
| Página em branco | Verificar `VITE_API_URL` nas variáveis de ambiente |
| CORS Error | Configurar CORS no backend para permitir o domínio |
| 404 nas rotas | Já configurado no `nginx.conf`, reconstruir imagem |
| SSL não funciona | Ativar Let's Encrypt no Dokploy |

---

**Tempo estimado de deploy**: 5-10 minutos  
**Última atualização**: 29/12/2025
