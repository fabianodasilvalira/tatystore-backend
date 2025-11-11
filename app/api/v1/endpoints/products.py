from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.product import Product
from app.models.company import Company
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.pagination import PaginatedResponse, paginate
from app.core.storage_local import save_company_file

router = APIRouter()


@router.get("/search", response_model=List[dict], summary="Buscar produtos para venda")
def search_products(
        q: str = "",
        limit: int = 50,
        active_only: bool = True,
        category_id: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Buscar Produtos para Venda**

    Endpoint otimizado para busca rápida de produtos durante vendas.
    Busca por nome, código de barras, SKU ou marca.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `q`: Termo de busca (nome, código, SKU, marca)
    - `active_only`: Se True, retorna apenas produtos ativos (padrão: True)
    - `category_id`: Filtrar por categoria (opcional)
    - `limit`: Quantidade de resultados (padrão: 50, máximo: 200)

    **Retorna:** Lista simplificada com campos essenciais para venda
    """
    if limit > 200:
        limit = 200

    query = db.query(Product).filter(Product.company_id == current_user.company_id)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Busca case-insensitive em múltiplos campos
    if q:
        search_filter = (
                Product.name.ilike(f"%{q}%") |
                Product.barcode.ilike(f"%{q}%") |
                Product.sku.ilike(f"%{q}%") |
                Product.brand.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    products = query.order_by(Product.name.asc()).limit(limit).all()

    # Retornar apenas campos essenciais para performance
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.sale_price),
            "stock_quantity": p.stock_quantity,
            "barcode": p.barcode,
            "sku": p.sku,
            "brand": p.brand,
            "image_url": p.image_url,
            "is_active": p.is_active,
            "min_stock": p.min_stock,
            "category_id": p.category_id,
            "is_on_sale": p.is_on_sale,
            "promotional_price": float(p.promotional_price) if p.promotional_price else None
        }
        for p in products
    ]


@router.get("/low-stock", response_model=List[dict], summary="Produtos com baixo estoque")
def get_low_stock_products(
        category_id: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos com Baixo Estoque**

    Retorna lista de produtos com estoque abaixo do mínimo.

    **Parâmetros:**
    - `category_id`: Filtrar por categoria (opcional)
    """
    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.stock_quantity <= Product.min_stock
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.stock_quantity.asc()).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "stock_quantity": p.stock_quantity,
            "min_stock": p.min_stock,
            "category_id": p.category_id,
            "image_url": p.image_url,
            "brand": p.brand,
            "sku": p.sku
        }
        for p in products
    ]


@router.get("/on-sale", response_model=List[dict], summary="Produtos em promoção")
def get_products_on_sale(
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos em Promoção**

    Retorna lista de produtos que estão em promoção.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `category_id`: Filtrar por categoria (opcional)

    **Útil para:** Criar seção de promoções no site/app
    """
    if limit > 200:
        limit = 200

    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.is_on_sale == True
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.offset(skip).limit(limit).all()

    from app.schemas.product import ProductResponse
    return [ProductResponse.model_validate(p).model_dump() for p in products]


@router.get("/", response_model=List[dict], summary="Listar produtos da empresa")
def list_products(
        skip: int = 0,
        limit: int = 10,
        active_only: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Listar Produtos da Empresa**

    Lista todos os produtos da empresa do usuário autenticado.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `active_only`: Se True, retorna apenas produtos ativos (padrão: False)
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 1000)

    **Resposta:** Lista de produtos com marca e imagem

    **Nota:** Para buscar produtos durante vendas, use /search
    """
    if limit > 1000:
        limit = 1000

    query = db.query(Product).filter(Product.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Product.is_active == True)

    products = query.offset(skip).limit(limit).all()

    products_data = [ProductResponse.model_validate(product).model_dump() for product in products]

    return products_data


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo produto")
def create_product(
        product_data: ProductCreate,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Cadastrar Novo Produto**

    Cria um novo produto vinculado à empresa do usuário autenticado.

    **Requer:** Admin ou Gerente

    **Controle de Estoque:** O estoque inicial é definido no cadastro

    **Campos Opcionais:**
    - `brand`: Marca do produto
    - `sku`: Código SKU
    - `barcode`: Código de barras
    - `description`: Descrição detalhada
    """
    # Criar produto
    product = Product(
        **product_data.model_dump(),
        company_id=current_user.company_id
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/{product_id}", response_model=ProductResponse, summary="Obter dados do produto")
def get_product(
        product_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Obter Dados de um Produto**

    Retorna informações detalhadas de um produto incluindo marca e imagem.

    **Isolamento:** Apenas produtos da mesma empresa
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    # Verificar isolamento de empresa
    if product.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse, summary="Atualizar produto")
def update_product(
        product_id: int,
        product_data: ProductUpdate,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Atualizar Produto**

    Atualiza informações de um produto incluindo marca.

    **Requer:** Admin ou Gerente

    **Nota:** Para ajustar estoque, use as vendas (débito automático)
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    # Verificar isolamento
    if product.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    # Atualizar campos
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar produto")
def delete_product(
        product_id: int,
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Desativar Produto**

    Desativa um produto (soft delete).

    **Requer:** Admin ou Gerente
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    # Verificar isolamento
    if product.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    product.is_active = False
    db.commit()

    return None


@router.post("/{product_id}/image", response_model=ProductResponse, summary="Upload de imagem do produto")
async def upload_product_image(
        product_id: int,
        file: UploadFile = File(...),
        current_user: User = Depends(require_role("admin", "gerente")),
        db: Session = Depends(get_db)
):
    """
    **Upload de Imagem do Produto**

    Faz upload da imagem do produto.

    **Requer:** Admin ou Gerente

    **Formatos Aceitos:** JPG, PNG, WEBP

    **Tamanho Máximo:** 5MB

    **Arquivo salvo em:** `/uploads/{company_slug}/products/`

    **Retorna:** Dados completos do produto com a URL da imagem atualizada
    """
    # Buscar produto
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    # Verificar isolamento
    if product.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    # Validar tipo de arquivo
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas JPG, PNG e WEBP são permitidos"
        )

    # Validar tamanho do arquivo (5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo 5MB"
        )

    company = db.query(Company).filter(Company.id == product.company_id).first()

    # Gerar nome único para o arquivo
    file_extension = file.filename.split(".")[-1]
    filename = f"product_{product_id}_{int(datetime.utcnow().timestamp())}.{file_extension}"

    image_url = save_company_file(
        company_slug=company.slug,
        folder="products",
        filename=filename,
        file_bytes=contents
    )

    # Atualizar URL da imagem no produto
    product.image_url = image_url
    db.commit()
    db.refresh(product)

    return product


@router.get("/by-category/{category_id}", response_model=List[dict], summary="Produtos por categoria")
def get_products_by_category(
        category_id: int,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos por Categoria**

    Lista produtos de uma categoria específica.

    **Isolamento:** Apenas produtos da mesma empresa
    """
    if limit > 200:
        limit = 200

    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.category_id == category_id
    )

    if active_only:
        query = query.filter(Product.is_active == True)

    products = query.offset(skip).limit(limit).all()

    from app.schemas.product import ProductResponse
    return [ProductResponse.model_validate(p).model_dump() for p in products]
