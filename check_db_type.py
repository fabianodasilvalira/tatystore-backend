import sys
import os

# Adiciona diretório atual ao path
sys.path.append(os.getcwd())

from app.core.config import settings

print(f"DATABASE_URL: {settings.DATABASE_URL}")
