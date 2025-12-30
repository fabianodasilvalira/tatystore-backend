# 🚀 DEPLOY RÁPIDO - TatyStore Frontend

## ✅ TUDO JÁ ESTÁ CONFIGURADO PARA PRODUÇÃO!

Você só precisa:
1. Fazer push para o Git
2. Configurar no Dokploy
3. Deploy automático!

---

## 📋 PASSO 1: Push para Git (2 minutos)

```bash
# 1. Adicionar todos os arquivos
git add .

# 2. Fazer commit
git commit -m "Frontend dockerizado e pronto para produção"

# 3. Push para o repositório
git push origin main
```

---

## 🔧 PASSO 2: Configurar no Dokploy (5 minutos)

### 2.1 Criar Projeto
1. Acesse o painel do Dokploy
2. Clique em "New Project"
3. Nome: `tatystore-frontend`

### 2.2 Conectar Git
1. Tipo: `Docker Compose`
2. Repository: `seu-repositorio-git`
3. Branch: `main`
4. Docker Compose Path: `docker-compose.yml`

### 2.3 Configurar Variáveis de Ambiente

**OBRIGATÓRIA:**
```
GEMINI_API_KEY=sua_chave_real_aqui
```

**Opcionais (já têm valores padrão):**
```
VITE_API_URL=https://tatystore.cloud
NODE_ENV=production
PORT=80
```

### 2.4 Configurar Domínio (Opcional)
1. Adicionar domínio customizado
2. Ativar SSL/HTTPS (Let's Encrypt automático)

---

## 🚀 PASSO 3: Deploy (1 clique)

1. Clique em **"Deploy"**
2. Aguarde 2-5 minutos (primeira build)
3. Pronto! ✅

---

## ✅ CHECKLIST PRÉ-DEPLOY

- [x] Dockerfile otimizado
- [x] docker-compose.yml configurado
- [x] nginx.conf com segurança
- [x] Variáveis de ambiente documentadas
- [x] Build testado localmente
- [x] Health checks configurados
- [x] Segurança implementada
- [ ] **Push para Git** ⚠️
- [ ] **GEMINI_API_KEY no Dokploy** ⚠️
- [ ] **SSL ativado** ⚠️

---

## 🔐 IMPORTANTE: Variáveis de Ambiente

### No Dokploy, adicione:

```env
GEMINI_API_KEY=sua_chave_real_aqui
```

**⚠️ NUNCA commite a chave no código!**

---

## 📊 O Que Vai Acontecer no Deploy

1. **Dokploy clona o repositório**
2. **Executa:** `docker-compose build tatystore_frontend`
3. **Build da aplicação** (2-5 minutos)
4. **Inicia o container**
5. **Health check** verifica se está saudável
6. **Aplicação no ar!** 🎉

---

## 🌐 Após o Deploy

### Verificar se está funcionando:

```bash
# Testar aplicação
curl https://seudominio.com

# Verificar headers de segurança
curl -I https://seudominio.com

# Verificar SSL
# https://www.ssllabs.com/ssltest/analyze.html?d=seudominio.com
```

### No Dokploy:
- Ver logs em tempo real
- Monitorar CPU e memória
- Ver status do health check

---

## 🆘 Troubleshooting

### Container não inicia?
```bash
# Ver logs no Dokploy
# Ou via SSH:
docker logs tatystore_frontend
```

### Erro 502 Bad Gateway?
- Verificar se container está rodando
- Verificar health check
- Ver logs de erro

### Variáveis não carregam?
- Verificar se estão configuradas no Dokploy
- Fazer redeploy

---

## 📝 Comandos Úteis (SSH no Servidor)

```bash
# Ver container rodando
docker ps | grep tatystore_frontend

# Ver logs
docker logs -f tatystore_frontend

# Ver status
docker inspect tatystore_frontend

# Reiniciar
docker restart tatystore_frontend
```

---

## 🎯 RESUMO

**Você precisa fazer:**
1. ✅ `git push origin main`
2. ✅ Criar projeto no Dokploy
3. ✅ Adicionar `GEMINI_API_KEY`
4. ✅ Clicar em "Deploy"

**Tempo total:** 10-15 minutos

**Resultado:** Aplicação no ar com HTTPS! 🚀

---

## 📚 Documentação Completa

- **[DEPLOY.md](DEPLOY.md)** - Guia detalhado
- **[SECURITY-CHECKLIST.md](SECURITY-CHECKLIST.md)** - Checklist de segurança
- **[CONTAINER-ID.md](CONTAINER-ID.md)** - Como identificar o container

---

**Tudo pronto!** Pode fazer o push para o Git agora! 🎉
