# ⚙️ Configuração de Variáveis de Ambiente - Dokploy

## 📋 Variáveis Necessárias

Copie e cole estas variáveis no painel do Dokploy em **Environment Variables**:

```env
# ============================================
# OBRIGATÓRIAS
# ============================================

# Chave da API Gemini (OBRIGATÓRIA)
# Obtenha em: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=sua_chave_api_aqui

# ============================================
# CONFIGURAÇÕES DO BACKEND
# ============================================

# URL do Backend (já está rodando em produção)
VITE_API_URL=https://tatystore.cloud

# ============================================
# CONFIGURAÇÕES DE AMBIENTE
# ============================================

# Ambiente de produção
NODE_ENV=production

# Porta do container (padrão Nginx)
PORT=80
```

---

## 🔑 Como Obter a GEMINI_API_KEY

1. Acesse: https://aistudio.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em **"Create API Key"**
4. Copie a chave gerada
5. Cole no campo `GEMINI_API_KEY` acima

---

## 📝 Instruções de Configuração no Dokploy

### **Método 1: Interface Web (Recomendado)**

1. Acesse o painel do Dokploy
2. Selecione o projeto `tatystore-frontend`
3. Vá em **Settings** → **Environment Variables**
4. Clique em **"Add Variable"** para cada variável
5. Cole os valores acima
6. Clique em **"Save"**
7. Faça um **Redeploy** para aplicar as mudanças

### **Método 2: Arquivo .env (Alternativo)**

Se o Dokploy suportar upload de arquivo `.env`:

1. Crie um arquivo `.env` com o conteúdo acima
2. Faça upload no painel do Dokploy
3. Salve e faça redeploy

---

## ✅ Verificação

Após configurar as variáveis:

1. ✅ Verifique se todas as 4 variáveis estão listadas
2. ✅ Certifique-se de que `GEMINI_API_KEY` não está vazia
3. ✅ Confirme que `VITE_API_URL` aponta para `https://tatystore.cloud`
4. ✅ Faça um **Redeploy** do projeto

---

## ⚠️ IMPORTANTE

- **NUNCA** commite o arquivo `.env` com a `GEMINI_API_KEY` real no Git
- Mantenha a chave da API em segredo
- Se a chave vazar, gere uma nova imediatamente em https://aistudio.google.com/app/apikey

---

## 🔍 Troubleshooting

### **Problema: Variáveis não estão sendo aplicadas**

**Solução**:
1. Certifique-se de ter clicado em **"Save"**
2. Faça um **Redeploy** completo (não apenas restart)
3. Verifique os logs para confirmar que as variáveis foram carregadas

### **Problema: "GEMINI_API_KEY is not defined"**

**Solução**:
1. Verifique se a variável está configurada no Dokploy
2. Certifique-se de que o nome está exatamente `GEMINI_API_KEY` (case-sensitive)
3. Faça um redeploy completo

### **Problema: Frontend não consegue conectar ao backend**

**Solução**:
1. Verifique se `VITE_API_URL=https://tatystore.cloud` está configurada
2. Teste o backend diretamente: `https://tatystore.cloud/docs`
3. Verifique as configurações de CORS no backend

---

**Última atualização**: 29/12/2025
