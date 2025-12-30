import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

# Forçar URL do banco localhost para script rodar fora do container
# Assumindo porta 5432 exposta
DB_URL = "postgresql://postgres:postgres@localhost:5432/tatystore"

def fix_company_logo():
    print(f"🔧 Conectando ao banco de dados...")
    engine = create_engine(DB_URL)
    
    logo_path = "uploads/taty/company/logo.png"
    logo_url = f"{settings.API_BASE_URL}/{logo_path}"
    # Ajuste para localhost se API_BASE_URL for https://tatystore.cloud
    if "tatystore.cloud" in logo_url:
        logo_url = f"http://localhost:8080/{logo_path}"
    
    try:
        with engine.connect() as conn:
            # 1. Buscar empresa Taty
            result = conn.execute(text("SELECT id, name FROM companies WHERE slug = 'taty'"))
            company = result.fetchone()
            
            if not company:
                print("❌ Empresa 'taty' não encontrada!")
                return

            print(f"🏢 Empresa encontrada: {company.name} (ID: {company.id})")
            
            # 2. Atualizar logo
            print(f"🔄 Atualizando logo para: {logo_path}")
            conn.execute(
                text("UPDATE companies SET logo = :logo WHERE id = :id"),
                {"logo": logo_path, "id": company.id}
            )
            conn.commit()
            print("✅ Logo atualizado com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    fix_company_logo()
