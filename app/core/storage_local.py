from pathlib import Path
from app.core.config import get_settings

settings = get_settings()

def save_company_file(company_slug: str, folder: str, filename: str, file_bytes: bytes) -> str:
    """
    Salva arquivo dentro do diretório da empresa e retorna uma URL ACESSÍVEL pelo frontend.
    Garante segurança, criação de pastas e compatibilidade com Docker.
    """

    base = Path(settings.UPLOAD_DIR)  # Ex: "uploads"
    target = base / company_slug / folder
    target.mkdir(parents=True, exist_ok=True)

    # Garantir nome seguro
    safe = filename.replace("..", "").replace("/", "_").replace("\\", "_")

    fp = target / safe

    # Salva o arquivo
    with open(fp, "wb") as f:
        f.write(file_bytes)

    # URL relativa (Melhor para previnir erros de concatenação no frontend)
    public_url = f"/uploads/{company_slug}/{folder}/{safe}"

    return public_url
