# 🏷️ Identificação do Container - TatyStore Frontend

## 📋 Informações do Container

### Nome do Container
```
tatystore_frontend
```

### Nome do Serviço (Docker Compose)
```
tatystore_frontend
```

---

## 🔍 Como Identificar o Container

### 1. Listar Containers Rodando

```bash
# Ver todos os containers
docker ps

# Procurar especificamente o TatyStore Frontend
docker ps | grep tatystore_frontend
```

**Saída esperada:**
```
CONTAINER ID   IMAGE                    COMMAND                  CREATED         STATUS                   PORTS                NAMES
abc123def456   tatystore_frontend:latest   "nginx -g 'daemon of…"   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:80->80/tcp   tatystore_frontend
```

### 2. Filtrar por Labels

```bash
# Filtrar por projeto
docker ps --filter "label=com.tatystore.project=tatystore"

# Filtrar por componente
docker ps --filter "label=com.tatystore.component=frontend"

# Filtrar por ambiente
docker ps --filter "label=com.tatystore.environment=production"
```

### 3. Ver Informações Detalhadas

```bash
# Inspecionar o container
docker inspect tatystore_frontend

# Ver apenas os labels
docker inspect tatystore_frontend | grep -A 20 "Labels"
```

---

## 🏷️ Labels Configurados

O container possui os seguintes labels para fácil identificação:

| Label | Valor | Descrição |
|-------|-------|-----------|
| `com.tatystore.project` | `tatystore` | Nome do projeto |
| `com.tatystore.component` | `frontend` | Componente (frontend/backend) |
| `com.tatystore.environment` | `production` | Ambiente de execução |
| `com.tatystore.version` | `1.0.0` | Versão da aplicação |
| `com.tatystore.tech-stack` | `react,vite,nginx,typescript` | Tecnologias usadas |
| `com.tatystore.description` | `TatyStore Frontend - Interface do usuário` | Descrição |
| `com.tatystore.maintainer` | `Fabiano Lira` | Responsável |
| `com.tatystore.build-date` | `2025-12-29` | Data do build |

---

## 📊 Comandos Úteis de Identificação

### Ver Logs do Container

```bash
# Logs em tempo real
docker logs -f tatystore_frontend

# Últimas 100 linhas
docker logs --tail 100 tatystore_frontend

# Logs com timestamp
docker logs -t tatystore_frontend
```

### Ver Status e Health Check

```bash
# Status geral
docker ps --filter "name=tatystore_frontend"

# Health check detalhado
docker inspect tatystore_frontend | grep -A 10 "Health"
```

### Ver Recursos Utilizados

```bash
# CPU, memória, rede, I/O
docker stats tatystore_frontend

# Apenas uma vez (não fica monitorando)
docker stats --no-stream tatystore_frontend
```

### Acessar o Container

```bash
# Abrir shell no container
docker exec -it tatystore_frontend sh

# Executar comando específico
docker exec tatystore_frontend whoami
# Esperado: appuser

# Ver processos rodando
docker exec tatystore_frontend ps aux
```

---

## 🔧 Comandos Docker Compose

### Gerenciar o Serviço

```bash
# Iniciar
docker-compose up tatystore_frontend

# Iniciar em background
docker-compose up -d tatystore_frontend

# Parar
docker-compose stop tatystore_frontend

# Reiniciar
docker-compose restart tatystore_frontend

# Ver logs
docker-compose logs -f tatystore_frontend

# Ver status
docker-compose ps tatystore_frontend
```

### Build e Rebuild

```bash
# Build
docker-compose build tatystore_frontend

# Rebuild sem cache
docker-compose build --no-cache tatystore_frontend

# Build e iniciar
docker-compose up --build tatystore_frontend
```

---

## 🌐 No Dokploy

### Como Identificar no Painel

1. **Nome do Container:** `tatystore_frontend`
2. **Labels visíveis:**
   - Project: `tatystore`
   - Component: `frontend`
   - Environment: `production`

### Filtros Úteis no Dokploy

- Filtrar por projeto: `tatystore`
- Filtrar por componente: `frontend`
- Filtrar por ambiente: `production`

---

## 📝 Exemplos Práticos

### Verificar se o Container Está Rodando

```bash
# Método 1: Por nome
docker ps | grep tatystore_frontend

# Método 2: Por label
docker ps --filter "label=com.tatystore.component=frontend"

# Método 3: Docker Compose
docker-compose ps tatystore_frontend
```

### Ver Informações Completas

```bash
# Todas as informações do container
docker inspect tatystore_frontend

# Apenas labels
docker inspect tatystore_frontend --format='{{json .Config.Labels}}' | jq

# Apenas status de saúde
docker inspect tatystore_frontend --format='{{json .State.Health}}' | jq
```

### Monitorar em Tempo Real

```bash
# Logs em tempo real
docker logs -f tatystore_frontend

# Stats em tempo real
docker stats tatystore_frontend

# Eventos do Docker
docker events --filter "container=tatystore_frontend"
```

---

## 🎯 Identificação Rápida

### Pergunta: "Qual container é o frontend?"

**Resposta:**
```bash
docker ps --filter "label=com.tatystore.component=frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Saída:**
```
NAMES                STATUS                   PORTS
tatystore_frontend   Up 10 minutes (healthy)  0.0.0.0:80->80/tcp
```

### Pergunta: "O container está saudável?"

**Resposta:**
```bash
docker inspect tatystore_frontend --format='{{.State.Health.Status}}'
```

**Saída esperada:**
```
healthy
```

### Pergunta: "Qual versão está rodando?"

**Resposta:**
```bash
docker inspect tatystore_frontend --format='{{index .Config.Labels "com.tatystore.version"}}'
```

**Saída:**
```
1.0.0
```

---

## 🚀 Resumo

**Nome do Container:** `tatystore_frontend`

**Como identificar rapidamente:**
```bash
docker ps | grep tatystore_frontend
```

**Como ver detalhes:**
```bash
docker inspect tatystore_frontend
```

**Como ver logs:**
```bash
docker logs -f tatystore_frontend
```

**Como acessar:**
```bash
docker exec -it tatystore_frontend sh
```

---

**Atualizado:** 2025-12-29  
**Versão:** 1.0.0
