# ============================================
# DOCKERFILE - TATYSTORE FRONTEND
# ============================================
# Este Dockerfile usa multi-stage build para criar uma imagem otimizada
# Estágio 1: Builder - Compila a aplicação React/TypeScript
# Estágio 2: Production - Serve os arquivos com Nginx
# ============================================

# ============================================
# ESTÁGIO 1: BUILDER
# ============================================
# Usa Node.js 20 Alpine (versão leve do Linux)
FROM node:20-alpine AS builder

# Instala dependências necessárias para compilar pacotes nativos
# python3, make, g++ são necessários para alguns pacotes npm
RUN apk add --no-cache python3 make g++

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas os arquivos de dependências primeiro
# Isso permite que o Docker use cache se as dependências não mudarem
COPY package.json package-lock.json* ./

# Instala TODAS as dependências (incluindo devDependencies)
# --production=false garante que dependências de desenvolvimento sejam instaladas
# Necessário para fazer o build da aplicação
RUN npm install --production=false

# Copia todo o código fonte da aplicação
COPY . .

# Executa o build de produção
# Vite compila TypeScript, minifica JS/CSS e otimiza assets
# Resultado fica na pasta /app/dist
RUN npm run build

# Remove dependências de desenvolvimento para reduzir tamanho
# Mantém apenas dependências de produção
RUN npm prune --production

# ============================================
# ESTÁGIO 2: PRODUCTION
# ============================================
# Usa Nginx Alpine (servidor web leve e rápido)
FROM nginx:alpine AS production

# ------------------------------------------
# LABELS (METADADOS DA IMAGEM)
# ------------------------------------------
# Informações para identificação no Docker e Dokploy
LABEL com.tatystore.project="tatystore" \
    com.tatystore.component="frontend" \
    com.tatystore.environment="production" \
    com.tatystore.version="1.0.0" \
    com.tatystore.tech-stack="react,vite,nginx,typescript" \
    com.tatystore.description="TatyStore Frontend - Interface do usuário" \
    com.tatystore.maintainer="Fabiano Lira" \
    com.tatystore.build-date="2025-12-29"

# Instala curl para health checks
# Permite verificar se o container está saudável
RUN apk add --no-cache curl

# Remove configuração padrão do Nginx
# Vamos usar nossa própria configuração customizada
RUN rm -rf /etc/nginx/conf.d/*

# Copia os arquivos compilados do estágio builder
# Apenas os arquivos estáticos (HTML, CSS, JS) vão para produção
# Código fonte TypeScript NÃO é incluído (segurança)
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia nossa configuração customizada do Nginx
# Inclui segurança, cache, compressão, etc.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ============================================
# SEGURANÇA: USUÁRIO NÃO-ROOT
# ============================================
# Cria um grupo e usuário não-root para rodar o Nginx
# UID/GID 1001 para evitar conflitos
# -S = usuário de sistema
# -D = sem senha
# -H = sem diretório home
RUN addgroup -g 1001 -S appuser && \
    adduser -S -D -H -u 1001 -h /usr/share/nginx/html -s /sbin/nologin -G appuser -g appuser appuser

# Ajusta permissões dos diretórios para o usuário appuser
# Necessário para que o Nginx possa escrever logs e cache
RUN chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid && \
    # Cria diretórios temporários do Nginx com permissões corretas
    mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    chown -R appuser:appuser /var/cache/nginx

# Modifica configuração do Nginx para rodar como appuser
# Por padrão, Nginx roda como root (inseguro)
RUN sed -i 's/user  nginx;/user  appuser;/' /etc/nginx/nginx.conf || true

# Expõe a porta 80 (HTTP)
# Dokploy vai mapear esta porta para o domínio público
EXPOSE 80

# ============================================
# HEALTH CHECK
# ============================================
# Verifica se o container está saudável a cada 30 segundos
# Se falhar 3 vezes seguidas, o container é marcado como unhealthy
# --interval=30s: verifica a cada 30 segundos
# --timeout=3s: aguarda no máximo 3 segundos por resposta
# --start-period=5s: aguarda 5 segundos antes da primeira verificação
# --retries=3: marca como unhealthy após 3 falhas consecutivas
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Muda para o usuário não-root
# A partir daqui, todos os comandos rodam como appuser (mais seguro)
USER appuser

# ============================================
# COMANDO DE INICIALIZAÇÃO
# ============================================
# Inicia o Nginx em modo foreground (daemon off)
# Necessário para que o Docker mantenha o container rodando
CMD ["nginx", "-g", "daemon off;"]

# ============================================
# RESUMO DO QUE ESTE DOCKERFILE FAZ:
# ============================================
# 1. Compila a aplicação React/TypeScript com Vite
# 2. Remove código fonte e dependências desnecessárias
# 3. Cria imagem final com apenas arquivos estáticos + Nginx
# 4. Configura usuário não-root para segurança
# 5. Adiciona health check para monitoramento
# 6. Resultado: Imagem ~25MB (vs ~450MB com node_modules)
# ============================================
