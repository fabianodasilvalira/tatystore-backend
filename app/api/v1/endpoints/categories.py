from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithProductCount
from app.schemas.pagination import paginate

router = APIRouter()


@router.get("/", summary="Listar categorias")
def list_categories(
        skip: int = 0,
        limit: Optional[int] = None,
        active_only: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Listar Categorias da Empresa**

    Lista todas as categorias da empresa do usuário autenticado.

    **Isolamento:** Apenas categorias da mesma empresa

    **Parâmetros:**
    - `active_only`: Se True, retorna apenas categorias ativas (padrão: False)
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Retorna:** Lista de categorias com contagem de produtos + metadados de paginação
    """
    query = db.query(
        Category,
        func.count(Product.id).label('product_count')
    ).outerjoin(
        Product,
        Product.category_id == Category.id
    ).filter(
        Category.company_id == current_user.company_id
    ).group_by(Category.id)

    if active_only:
        query = query.filter(Category.is_active == True)

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        results = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 200:
            limit = 200
        results = query.limit(limit).all()

    categories_data = [
        CategoryWithProductCount(
            **CategoryResponse.model_validate(category).model_dump(),
            product_count=count
        )
        for category, count in results
    ]

    return paginate(categories_data, total, skip, limit)


@router.get("/stats", summary="Estatísticas de categorias")
def get_categories_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Estatísticas Gerais de Categorias**

    Retorna estatísticas agregadas de todas as categorias.

    **Isolamento:** Apenas categorias da mesma empresa

    **Retorna:**
    - Total de categorias ativas
    - Total de produtos por categoria
    - Valor total de estoque por categoria
    - Categorias sem produtos
    """
    stats = db.query(
        Category.id,
        Category.name,
        func.count(Product.id).label('product_count'),
        func.coalesce(func.sum(Product.stock_quantity * Product.cost_price), 0).label('total_value'),
        func.coalesce(func.sum(Product.stock_quantity), 0).label('total_stock')
    ).outerjoin(
        Product,
        Product.category_id == Category.id
    ).filter(
        Category.company_id == current_user.company_id
    ).group_by(Category.id, Category.name).all()

    categories_data = [
        {
            "category_id": s.id,
            "category_name": s.name,
            "product_count": s.product_count,
            "total_stock_value": float(s.total_value),
            "total_stock_quantity": s.total_stock
        }
        for s in stats
    ]

    return {
        "total_categories": len(categories_data),
        "categories": categories_data,
        "empty_categories": [c for c in categories_data if c['product_count'] == 0]
    }


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Criar categoria")
def create_category(
        category_data: CategoryCreate,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Cadastrar Nova Categoria**

    Cria uma nova categoria vinculada à empresa do usuário autenticado.

    **Requer:** Admin ou Gerente

    **Exemplos de Categorias:**
    - Perfumes
    - Joias
    - Bolsas
    - Acessórios
    """
    # Verificar se já existe categoria com mesmo nome na empresa
    existing = db.query(Category).filter(
        Category.company_id == current_user.company_id,
        Category.name == category_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma categoria com este nome"
        )

    category = Category(
        **category_data.model_dump(),
        company_id=current_user.company_id
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/{category_id}", response_model=CategoryResponse, summary="Obter categoria")
def get_category(
        category_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Obter Dados de uma Categoria**

    Retorna informações detalhadas de uma categoria.

    **Isolamento:** Apenas categorias da mesma empresa
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    return category


@router.get("/{category_id}/stats", summary="Estatísticas detalhadas da categoria")
def get_category_stats(
        category_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Estatísticas Detalhadas de uma Categoria**

    Retorna análise completa de produtos de uma categoria.

    **Isolamento:** Apenas categorias da mesma empresa

    **Retorna:**
    - Total de produtos
    - Valor total do estoque
    - Produtos em promoção
    - Produtos com baixo estoque
    - Top 5 produtos mais valiosos
    """
    # Verificar se categoria existe e pertence à empresa
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    # Consulta de estatísticas
    products = db.query(Product).filter(
        Product.category_id == category_id,
        Product.company_id == current_user.company_id
    ).all()

    total_products = len(products)
    total_stock_value = sum(p.stock_quantity * p.cost_price for p in products)
    total_stock_quantity = sum(p.stock_quantity for p in products)
    products_on_sale = sum(1 for p in products if p.is_on_sale)
    products_low_stock = sum(1 for p in products if p.stock_quantity <= p.min_stock)

    # Top 5 produtos mais valiosos
    top_products = sorted(
        products,
        key=lambda p: p.stock_quantity * p.cost_price,
        reverse=True
    )[:5]

    return {
        "category_id": category.id,
        "category_name": category.name,
        "total_products": total_products,
        "total_stock_value": float(total_stock_value),
        "total_stock_quantity": total_stock_quantity,
        "products_on_sale": products_on_sale,
        "products_low_stock": products_low_stock,
        "top_products": [
            {
                "id": p.id,
                "name": p.name,
                "stock_value": float(p.stock_quantity * p.cost_price),
                "stock_quantity": p.stock_quantity
            }
            for p in top_products
        ]
    }


@router.put("/{category_id}", response_model=CategoryResponse, summary="Atualizar categoria")
def update_category(
        category_id: int,
        category_data: CategoryUpdate,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Atualizar Categoria**

    Atualiza informações de uma categoria.

    **Requer:** Admin ou Gerente
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    update_data = category_data.model_dump(exclude_unset=True)

    # Verificar duplicação de nome se estiver sendo alterado
    if 'name' in update_data:
        existing = db.query(Category).filter(
            Category.company_id == current_user.company_id,
            Category.name == update_data['name'],
            Category.id != category_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma categoria com este nome"
            )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar categoria")
def delete_category(
        category_id: int,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Desativar Categoria**

    Desativa uma categoria (soft delete).

    **Requer:** Admin ou Gerente

    **Nota:** Os produtos vinculados à categoria não serão afetados
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    category.is_active = False
    db.commit()

    return None


@router.get("/{category_id}/products", summary="Listar produtos da categoria")
def list_category_products(
        category_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        active_only: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Listar Produtos de uma Categoria**

    Lista todos os produtos vinculados a uma categoria.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `active_only`: Se True, retorna apenas produtos ativos (padrão: False)
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Retorna:** Lista de produtos com metadados de paginação
    """
    # Verificar se categoria existe e pertence à empresa
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    query = db.query(Product).filter(
        Product.category_id == category_id,
        Product.company_id == current_user.company_id
    )

    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        products = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 200:
            limit = 200
        products = query.limit(limit).all()

    from app.schemas.product import ProductResponse
    products_data = [ProductResponse.model_validate(p).model_dump() for p in products]

    return paginate(products_data, total, skip, limit)


@router.get("/{category_id}/products/on-sale", summary="Produtos em promoção da categoria")
def list_category_products_on_sale(
        category_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos em Promoção de uma Categoria**

    Lista apenas produtos em promoção de uma categoria específica.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Útil para:** Criar seções de promoções por categoria
    """
    # Verificar se categoria existe e pertence à empresa
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    query = db.query(Product).filter(
        Product.category_id == category_id,
        Product.company_id == current_user.company_id,
        Product.is_on_sale == True
    )

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        products = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 200:
            limit = 200
        products = query.limit(limit).all()

    from app.schemas.product import ProductResponse
    products_data = [ProductResponse.model_validate(p).model_dump() for p in products]

    return paginate(products_data, total, skip, limit)


@router.get("/{category_id}/products/low-stock", summary="Produtos com baixo estoque da categoria")
def list_category_products_low_stock(
        category_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos com Baixo Estoque de uma Categoria**

    Lista produtos com estoque abaixo do mínimo em uma categoria específica.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Útil para:** Identificar produtos para reposição por categoria
    """
    # Verificar se categoria existe e pertence à empresa
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )

    if category.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    query = db.query(Product).filter(
        Product.category_id == category_id,
        Product.company_id == current_user.company_id,
        Product.stock_quantity <= Product.min_stock
    ).order_by(Product.stock_quantity.asc())

    total = query.count()

    query = query.offset(skip)

    if limit is None:
        products = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 200:
            limit = 200
        products = query.limit(limit).all()

    products_data = [
        {
            "id": p.id,
            "name": p.name,
            "stock_quantity": p.stock_quantity,
            "min_stock": p.min_stock,
            "category_id": p.category_id
        }
        for p in products
    ]

    return paginate(products_data, total, skip, limit)
