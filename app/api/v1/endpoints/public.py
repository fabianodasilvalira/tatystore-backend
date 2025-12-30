"""
Endpoints Públicos (v1)
Sem autenticação - apenas visualização de produtos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.schemas.product import ProductPublicResponse
from app.schemas.pagination import paginate

router = APIRouter()


@router.get("/companies/{company_slug}/categories", summary="Listar categorias de uma empresa (público)")
async def list_company_categories(
    company_slug: str,
    db: Session = Depends(get_db)
):
    """
    **Listar Categorias Públicas**
    
    Lista categorias ativas de uma empresa pelo slug (sem autenticação).
    Útil para criar menus de navegação em sites/apps.
    
    **Parâmetros:**
    - `company_slug`: Slug único da empresa
    
    **Retorna:** Lista de categorias com contagem de produtos ativos
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
    
    # Buscar categorias com contagem de produtos
    from sqlalchemy import func
    categories = db.query(
        Category,
        func.count(Product.id).label('product_count')
    ).outerjoin(
        Product,
        (Product.category_id == Category.id) & (Product.is_active == True)
    ).filter(
        Category.company_id == company.id,
        Category.is_active == True
    ).group_by(Category.id).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "product_count": count
        }
        for cat, count in categories
    ]


@router.get("/companies/{company_slug}/products", summary="Listar produtos de uma empresa (público)")
async def list_company_products(
    company_slug: str,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    **Listar Produtos Públicos**
    
    Lista produtos de uma empresa pelo slug (sem autenticação).
    Útil para vitrine online.
    
    **Parâmetros:**
    - `company_slug`: Slug único da empresa
    - `search`: Buscar por nome
    - `category_id`: Filtrar por categoria
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Retorna:**
    - `items`: Produtos paginados
    - `metadata`: Informações de paginação
    - `promocao`: Array com TODOS os produtos em promoção (sem limite de paginação)
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

    # Query base para produtos ativos
    query = db.query(Product).filter(
        Product.company_id == company.id,
        Product.is_active == True
    )

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    total = query.count()

    if limit is None:
        limit = total if total > 0 else 1
        products = query.offset(skip).all()
    else:
        if limit > 1000:
            limit = 1000
        products = query.offset(skip).limit(limit).all()

    # Converter produtos para o schema público
    products_data = [ProductPublicResponse.model_validate(p).model_dump() for p in products]

    # Essa query sempre retorna todos os produtos em promoção da empresa, ignorando skip/limit
    promotion_query = db.query(Product).filter(
        Product.company_id == company.id,
        Product.is_active == True,
        Product.is_on_sale == True
    )

    products_on_promotion = promotion_query.all()
    promotion_data = [ProductPublicResponse.model_validate(p).model_dump() for p in products_on_promotion]

    # Retornar usando a função paginate para formato consistente, com array adicional de promoções
    response = paginate(products_data, total, skip, limit)
    response["promocao"] = promotion_data

    return response


@router.get("/companies/{company_slug}/categories/{category_id}/products", summary="Listar produtos de uma categoria (público)")
async def list_company_category_products(
    company_slug: str,
    category_id: int,
    skip: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    **Listar Produtos Públicos de uma Categoria**

    Lista produtos de uma categoria específica sem autenticação.
    Útil para páginas de categoria em sites/apps.

    **Parâmetros:**
    - `company_slug`: Slug único da empresa
    - `category_id`: ID da categoria
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
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

    # Verificar se categoria existe
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.company_id == company.id,
        Category.is_active == True
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    query = db.query(Product).filter(
        Product.company_id == company.id,
        Product.category_id == category_id,
        Product.is_active == True
    )

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        products = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 1000:
            limit = 1000
        products = query.limit(limit).all()
    
    return [ProductPublicResponse.model_validate(p).model_dump() for p in products]


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


@router.get("/companies/slug/{company_slug}", summary="Obter dados públicos da empresa")
async def get_public_company(
        company_slug: str,
        db: Session = Depends(get_db)
):
    """
    **Obter Dados Públicos da Empresa pelo SLUG (Sem autenticação)**

    Retorna informações básicas da empresa se ela estiver ativa.

    **Parâmetros:**
    - `company_slug`: Slug único da empresa

    **Retorna:** Dados públicos da empresa
    """
    company = db.query(Company).filter(
        Company.slug == company_slug,
        Company.is_active == True
    ).first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada ou inativa"
        )

    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "logo_url": company.logo_url,
        "created_at": company.created_at,
        "is_active": company.is_active
    }



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

@router.get("/version", summary="Verificar versão da API")
def get_api_version():
    """
    **Verificar Versão**
    
    Retorna o timestamp da versão atual para validar deploy.
    """
    from app.core.datetime_utils import get_now_fortaleza_naive
    return {
        "version": "1.0.1",
        "timestamp": get_now_fortaleza_naive(),
        "environment": "production",
        "last_update": "Fix Routing & Import"
    }
