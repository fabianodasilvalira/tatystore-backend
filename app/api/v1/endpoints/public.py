"""
Endpoints Públicos (v1)
Sem autenticação - apenas visualização de produtos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.product import Product
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.schemas.product import ProductPublicResponse

router = APIRouter()


@router.get("/companies/{company_slug}/products", response_model=List[ProductPublicResponse], summary="Listar produtos de uma empresa (público)")
async def list_company_products(
    company_slug: str,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    **Listar Produtos Públicos**
    
    Lista produtos de uma empresa pelo slug (sem autenticação).
    Útil para vitrine online.
    
    **Parâmetros:**
    - `company_slug`: Slug único da empresa
    - `search`: Buscar por nome
    """
    company = db.query(Company).filter(
        Company.slug == company_slug,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    query = db.query(Product).filter(
        Product.company_id == company.id,
        Product.is_active == True
    )
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    products = query.offset(skip).limit(limit).all()
    
    return products


@router.get("/companies/{company_slug}/products/{product_id}", response_model=ProductPublicResponse, summary="Obter detalhes de um produto (público)")
async def get_company_product(
    company_slug: str,
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    **Obter Produto Público**
    
    Retorna detalhes de um produto específico sem autenticação.
    """
    company = db.query(Company).filter(
        Company.slug == company_slug,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == company.id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return product


@router.get("/test-credentials", summary="Ver credenciais de teste")
def get_test_credentials(db: Session = Depends(get_db)):
    """
    **Ver Credenciais de Teste**
    
    Retorna todas as credenciais de usuários de teste para facilitar testes.
    ATENÇÃO: Este endpoint deve ser REMOVIDO em produção!
    """
    users = db.query(User).join(Company).join(Role).filter(User.is_active == True).all()
    
    credentials = []
    for user in users:
        # Determinar senha com base no email
        if "admin" in user.email:
            senha = "admin123"
        elif "gerente" in user.email:
            senha = "gerente123"
        else:
            senha = "vendedor123"
        
        credentials.append({
            "email": user.email,
            "senha": senha,
            "empresa": user.company.name,
            "empresa_slug": user.company.slug,
            "perfil": user.role.name,
            "ativo": user.is_active,
            "pode_logar": user.is_active and user.company.is_active
        })
    
    return {
        "mensagem": "Use essas credenciais para testar o login no endpoint POST /api/v1/auth/login-json",
        "total_usuarios": len(credentials),
        "credenciais": credentials,
        "exemplo_request": {
            "url": "/api/v1/auth/login-json",
            "method": "POST",
            "body": {
                "email": "admin@taty.com",
                "password": "admin123"
            }
        }
    }
