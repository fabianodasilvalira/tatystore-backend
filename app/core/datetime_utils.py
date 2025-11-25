"""
Utilitários de Data/Hora com timezone configurável para Fortaleza - CE
Centraliza a manipulação de datas no sistema para garantir consistência
"""
from datetime import datetime, timezone, timedelta
import pytz
from app.core.config import settings

# Timezone de Fortaleza (UTC-3)
FORTALEZA_TZ = pytz.timezone('America/Fortaleza')

# Timezone UTC para comparações
UTC_TZ = pytz.UTC


def get_now_fortaleza() -> datetime:
    """
    Retorna o datetime atual no timezone de Fortaleza com timezone info
    Usado para criar novos registros no banco
    """
    return datetime.now(FORTALEZA_TZ)


def get_now_fortaleza_naive() -> datetime:
    """
    Retorna o datetime atual no timezone de Fortaleza SEM timezone info
    Compatível com código legado que usa datetime.utcnow()
    """
    return datetime.now(FORTALEZA_TZ).replace(tzinfo=None)


def get_now_utc() -> datetime:
    """
    Retorna o datetime atual em UTC com timezone info
    Mantém compatibilidade com código que usa UTC
    """
    return datetime.now(UTC_TZ)


def localize_to_fortaleza(dt: datetime) -> datetime:
    """
    Converte um datetime naive ou UTC para timezone de Fortaleza
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Assumir que é UTC se for naive
        dt = UTC_TZ.localize(dt)
    
    return dt.astimezone(FORTALEZA_TZ)


def format_datetime_fortaleza(dt: datetime, format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
    """
    Formata um datetime para o padrão brasileiro em Fortaleza
    Exemplo: "25/11/2025 14:30:45"
    """
    if dt is None:
        return None
    
    fortaleza_dt = localize_to_fortaleza(dt)
    return fortaleza_dt.strftime(format_str)


def default_datetime_fortaleza() -> datetime:
    """
    Wrapper callable para usar em Column(DateTime, default=default_datetime_fortaleza)
    SQLAlchemy chama essa função a cada novo registro
    """
    return get_now_fortaleza_naive()
