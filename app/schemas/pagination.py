from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field, ConfigDict
from math import ceil

T = TypeVar('T')

class PaginationMetadata(BaseModel):
    """Metadados de paginação"""
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página atual")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Tem próxima página")
    has_prev: bool = Field(..., description="Tem página anterior")

class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica"""
    model_config = ConfigDict(from_attributes=True)
    
    data: List[T] = Field(..., description="Lista de dados")
    metadata: PaginationMetadata = Field(..., description="Metadados de paginação")

def paginate(data: List[T], total: int, skip: int, limit: int) -> dict:
    """
    Função auxiliar para criar resposta paginada
    
    Args:
        data: Lista de dados da página atual
        total: Total de registros no banco
        skip: Quantidade de registros pulados
        limit: Quantidade de registros por página
    
    Returns:
        Dicionário com data e metadata
    """
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": data,
        "metadata": {
            "total": total,
            "page": page,
            "per_page": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
