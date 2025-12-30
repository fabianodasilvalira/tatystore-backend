# 🎯 Configuração EXATA do Domínio no Dokploy

## 📊 Comparação: Backend vs Frontend

### ✅ BACKEND (Já Configurado - Funcionando)

```
┌─────────────────────────────────────────┐
│  BACKEND - tatystore.cloud              │
├─────────────────────────────────────────┤
│  Host:           tatystore.cloud        │
│  Path:           /                      │
│  Internal Path:  /                      │
│  Container Port: 8080                   │
│  HTTPS:          ✅ ON                  │
│  Certificate:    Let's Encrypt          │
└─────────────────────────────────────────┘

Resultado:
✅ https://tatystore.cloud/      → API raiz
✅ https://tatystore.cloud/docs  → Documentação
✅ https://tatystore.cloud/api   → Endpoints
```

### 🚀 FRONTEND (A Configurar - Mesma Estrutura)

```
┌─────────────────────────────────────────┐
│  FRONTEND - app.tatystore.cloud         │
├─────────────────────────────────────────┤
│  Host:           app.tatystore.cloud    │
│  Path:           /                      │
│  Internal Path:  /                      │
│  Container Port: 80                     │ ← DIFERENTE!
│  HTTPS:          ✅ ON                  │
│  Certificate:    Let's Encrypt          │
└─────────────────────────────────────────┘

Resultado:
✅ https://app.tatystore.cloud/  → Interface
```

---

## 🔧 PASSO A PASSO NO DOKPLOY

### **1. Acessar Configuração de Domínio**

1. No Dokploy, selecione o projeto `tatystore-frontend`
2. Vá em **"Domains"** ou **"Domain"** (mesmo lugar onde configurou o backend)
3. Clique em **"Add Domain"** ou **"Edit Domain"**

---

### **2. Preencher os Campos EXATAMENTE Assim**

Copie e cole estes valores **exatamente** como estão:

#### **Campo: Host / Hospedar**
```
app.tatystore.cloud
```
> ⚠️ **IMPORTANTE**: Use `app.tatystore.cloud`, NÃO use `tatystore.cloud` (esse já é do backend)

#### **Campo: Path / Caminho**
```
/
```
> ✅ Apenas uma barra `/` (igual ao backend)

#### **Campo: Internal Path / Caminho Interno**
```
/
```
> ✅ Apenas uma barra `/` (igual ao backend)

#### **Campo: Container Port / Porto de Contêineres**
```
80
```
> ⚠️ **ATENÇÃO**: Aqui é `80` (frontend usa Nginx na porta 80)
> 
> O backend usa `8080` porque é FastAPI
> 
> O frontend usa `80` porque é Nginx

#### **Campo: HTTPS**
```
✅ ATIVADO (toggle ON)
```
> ✅ Sempre ative HTTPS em produção

#### **Campo: Certificate Provider / Fornecedor de Certificados**
```
Let's Encrypt
```
> ✅ Mesmo do backend

---

## 📋 Tabela de Referência Rápida

| Campo | Backend | Frontend | Observação |
|-------|---------|----------|------------|
| **Host** | `tatystore.cloud` | `app.tatystore.cloud` | Domínios diferentes |
| **Path** | `/` | `/` | ✅ Igual |
| **Internal Path** | `/` | `/` | ✅ Igual |
| **Container Port** | `8080` | `80` | ⚠️ DIFERENTE! |
| **HTTPS** | ✅ ON | ✅ ON | ✅ Igual |
| **Certificate** | Let's Encrypt | Let's Encrypt | ✅ Igual |

---

## ⚠️ ERROS COMUNS A EVITAR

### ❌ **ERRO 1: Usar a mesma porta do backend**
```
Container Port: 8080  ← ERRADO para frontend!
```
✅ **CORRETO:**
```
Container Port: 80    ← Frontend usa Nginx na porta 80
```

### ❌ **ERRO 2: Usar o mesmo domínio do backend**
```
Host: tatystore.cloud  ← ERRADO! Já é do backend
```
✅ **CORRETO:**
```
Host: app.tatystore.cloud  ← Subdomínio para o frontend
```

### ❌ **ERRO 3: Colocar /api no path**
```
Path: /api  ← ERRADO! Isso é para o backend
```
✅ **CORRETO:**
```
Path: /     ← Frontend usa a raiz
```

---

## 🔍 Como Saber se Está Correto?

Depois de salvar, verifique:

### **Backend (já funcionando):**
- ✅ `https://tatystore.cloud/docs` → Abre a documentação Swagger
- ✅ `https://tatystore.cloud/health` → Retorna `{"status":"healthy"}`

### **Frontend (após configurar):**
- ✅ `https://app.tatystore.cloud/` → Abre a interface do TatyStore
- ✅ Sem erros de CORS no console (F12)

---

## 🌐 Configuração DNS (NÃO ESQUEÇA!)

Depois de configurar o domínio no Dokploy, você **PRECISA** configurar o DNS na Hostinger:

### **No Painel DNS da Hostinger:**

1. Vá em **"DNS / Name Servers"**
2. Clique em **"Add Record"** ou **"Adicionar Registro"**
3. Preencha:

| Campo | Valor |
|-------|-------|
| **Type / Tipo** | A |
| **Name / Nome** | `app` |
| **Points to / Aponta para** | `IP do servidor Dokploy` |
| **TTL** | 3600 |

4. Clique em **"Save"** ou **"Salvar"**
5. Aguarde 5-30 minutos para propagação

> 💡 **Como encontrar o IP do servidor?**
> - No Dokploy, vá em **Settings** ou **Server**
> - Ou use o mesmo IP que você usou para `tatystore.cloud`

---

## ✅ Checklist Final

Antes de fazer deploy, confirme:

- [ ] Host: `app.tatystore.cloud` ✅
- [ ] Path: `/` ✅
- [ ] Internal Path: `/` ✅
- [ ] Container Port: `80` ✅ (NÃO 8080!)
- [ ] HTTPS: Ativado ✅
- [ ] Certificate: Let's Encrypt ✅
- [ ] DNS configurado na Hostinger ✅
- [ ] Aguardou propagação DNS (5-30 min) ✅

---

## 🎯 Resumo Visual

```
┌──────────────────────────────────────────────────────┐
│                 ARQUITETURA FINAL                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🌐 FRONTEND                                         │
│     https://app.tatystore.cloud                      │
│     Porta: 80 (Nginx)                                │
│     Path: /                                          │
│                                                      │
│  🔧 BACKEND                                          │
│     https://tatystore.cloud                          │
│     Porta: 8080 (FastAPI)                            │
│     Path: /                                          │
│     Rotas: /api, /docs, /health                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 📞 Próximos Passos

1. ✅ Configurar domínio no Dokploy (use os valores acima)
2. ✅ Configurar DNS na Hostinger (registro A para `app`)
3. ✅ Aguardar propagação DNS (5-30 minutos)
4. ✅ Fazer deploy do frontend
5. ✅ Testar: `https://app.tatystore.cloud`

---

**Tempo estimado**: 5 minutos (+ 5-30 min de propagação DNS)  
**Dificuldade**: Fácil (só copiar e colar os valores)  
**Última atualização**: 29/12/2025
