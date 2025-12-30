<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/19Ky4P43-PUxBiJTsv3pbnAXevyzYmVXp

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## 🐳 Run with Docker

**Prerequisites:** Docker e Docker Compose

### Desenvolvimento (com hot-reload):
```bash
# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e adicione sua GEMINI_API_KEY

# 2. Inicie o container
docker-compose up tatystore-dev

# 3. Acesse em http://localhost:3000
```

> **💡 Nota:** O backend já está rodando em `https://tatystore.cloud/`. Veja [DOCKER-BACKEND.md](DOCKER-BACKEND.md) para detalhes sobre a integração.

### Produção (com Nginx):
```bash
docker-compose up tatystore-prod
# Acesse em http://localhost
```

📖 **Documentação completa:** Veja [DOCKER.md](DOCKER.md) para instruções detalhadas, troubleshooting e comandos úteis.
