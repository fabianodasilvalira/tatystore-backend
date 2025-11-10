from pathlib import Path
from app.core.config import get_settings
settings = get_settings()
def save_company_file(company_slug: str, folder: str, filename: str, file_bytes: bytes) -> str:
    base = Path(settings.upload_root)
    target = base / company_slug / folder
    target.mkdir(parents=True, exist_ok=True)
    safe = filename.replace("..","").replace("/","_").replace("\\","_")
    fp = target / safe
    with open(fp, "wb") as f:
        f.write(file_bytes)
    return f"/{settings.upload_root}/{company_slug}/{folder}/{safe}"
