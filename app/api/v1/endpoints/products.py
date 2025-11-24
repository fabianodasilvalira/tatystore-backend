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

def generate_sku(db: Session, company_id: int, product_name: str, category_id: Optional[int] = None) -> str:
    """
    Gera código SKU automaticamente seguindo o padrão:
    
    Formato: {CATEGORIA_SIGLA}-{PRIMEIRAS_LETRAS_PRODUTO}-{SEQUENCIAL}
    Exemplo: ELE-NOTE-001, ALI-ARRO-002, GER-CAFE-015
    
    Regras:
    - Categoria: 3 primeiras letras da categoria (uppercase) ou "GER" para produtos sem categoria
    - Produto: 4 primeiras letras do nome do produto (uppercase, removendo espaços)
    - Sequencial: Número sequencial de 3 dígitos baseado na quantidade de produtos da empresa
    """
    from app.models.category import Category
    
    # Obter sigla da categoria
    if category_id:
        category = db.query(Category).filter(Category.id == category_id).first()
        category_prefix = category.name[:3].upper() if category else "GER"
    else:
        category_prefix = "GER"
    
    # Obter primeiras letras do produto (remover espaços e caracteres especiais)
    product_clean = ''.join(c for c in product_name if c.isalnum() or c.isspace())
    product_words = product_clean.split()
    
    if len(product_words) >= 2:
        # Se tiver 2+ palavras, pegar 2 letras de cada uma das 2 primeiras
        product_prefix = (product_words[0][:2] + product_words[1][:2]).upper()
    else:
        # Se tiver 1 palavra, pegar as 4 primeiras letras
        product_prefix = product_clean[:4].upper()
    
    # Garantir que o prefixo do produto tenha 4 caracteres
    product_prefix = product_prefix.ljust(4, 'X')[:4]
    
    # Contar produtos da empresa para gerar sequencial
    product_count = db.query(Product).filter(Product.company_id == company_id).count()
    sequential = str(product_count + 1).zfill(3)
    
    # Gerar SKU
    sku = f"{category_prefix}-{product_prefix}-{sequential}"
    
    # Verificar se SKU já existe (improvável mas possível)
    existing = db.query(Product).filter(
        Product.company_id == company_id,
        Product.sku == sku
    ).first()
    
    # Se já existir, adicionar timestamp para garantir unicidade
    if existing:
        timestamp = str(int(datetime.utcnow().timestamp()))[-4:]
        sku = f"{category_prefix}-{product_prefix}-{timestamp}"
    
    return sku


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


@router.get("/search-by-barcode", response_model=dict, summary="Buscar produto por código de barras")
def search_by_barcode_query(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Buscar Produto por Código de Barras (Query Parameter)**
    
    Busca um produto pelo código de barras usando query parameter.
    
    **Isolamento:** Apenas produtos da mesma empresa
    
    **Parâmetros:**
    - `barcode`: Código de barras do produto
    
    **Retorna:** Dados do produto ou 404 se não encontrado
    
    **Exemplo:** GET /products/search-by-barcode?barcode=7891234567890
    """
    product = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.barcode == barcode
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return ProductResponse.model_validate(product).model_dump()


@router.get("/barcode/{barcode}", response_model=dict, summary="Buscar produto por código de barras (path)")
def search_by_barcode_path(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Buscar Produto por Código de Barras (Path Parameter)**
    
    Busca um produto pelo código de barras usando path parameter.
    
    **Isolamento:** Apenas produtos da mesma empresa
    
    **Parâmetros:**
    - `barcode`: Código de barras do produto
    
    **Retorna:** Dados do produto ou 404 se não encontrado
    
    **Exemplo:** GET /products/barcode/7891234567890
    """
    product = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.barcode == barcode
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    return ProductResponse.model_validate(product).model_dump()


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


@router.get("/on-sale", summary="Produtos em promoção")
def get_products_on_sale(
        skip: int = 0,
        limit: Optional[int] = None,
        category_id: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos em Promoção**

    Retorna lista de produtos que estão em promoção.

    **Isolamento:** Apenas produtos da mesma empresa

    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    - `category_id`: Filtrar por categoria (opcional)

    **Útil para:** Criar seção de promoções no site/app
    """
    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.is_on_sale == True
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    total = query.count()
    
    if limit is None:
        limit = total if total > 0 else 1
        products = query.offset(skip).all()
    else:
        if limit > 200:
            limit = 200
        products = query.offset(skip).limit(limit).all()

    return [ProductResponse.model_validate(p).model_dump() for p in products]


@router.get("/", summary="Listar produtos da empresa")
def list_products(
        skip: int = 0,
        limit: Optional[int] = None,
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
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)

    **Resposta:** Lista de produtos com marca e imagem

    **Nota:** Para buscar produtos durante vendas, use /search
    """
    query = db.query(Product).filter(Product.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()

    if limit is None:
        limit = total if total > 0 else 1
        products = query.offset(skip).all()
    else:
        if limit > 1000:
            limit = 1000
        products = query.offset(skip).limit(limit).all()

    return [ProductResponse.model_validate(product).model_dump() for product in products]


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo produto")
def create_product(
        product_data: ProductCreate,
        current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
        db: Session = Depends(get_db)
):
    """
    **Cadastrar Novo Produto**

    Cria um novo produto vinculado à empresa do usuário autenticado.
    
    **NOVIDADE:** O código SKU é gerado automaticamente se não for informado.
    
    **Formato SKU:** {CATEGORIA}-{PRODUTO}-{SEQUENCIAL}
    - Exemplo: ELE-NOTE-001, ALI-ARRO-002

    **Requer:** Admin, Gerente ou Vendedor

    **Controle de Estoque:** O estoque inicial é definido no cadastro

    **Campos Opcionais:**
    - `brand`: Marca do produto
    - `sku`: Código SKU (se não informado, será gerado automaticamente)
    - `barcode`: Código de barras
    - `description`: Descrição detalhada
    """
    if not product_data.sku:
        product_data.sku = generate_sku(
            db=db,
            company_id=current_user.company_id,
            product_name=product_data.name,
            category_id=product_data.category_id
        )
    
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


@router.get("/{product_id}/profit-analysis", summary="Análise de lucro do produto")
def get_product_profit_analysis(
        product_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Análise de Lucro do Produto**

    Calcula lucro e margem de lucro de um produto considerando:
    - Preço de venda normal vs preço de custo
    - Preço promocional vs preço de custo (se em promoção)

    **Isolamento:** Apenas produtos da mesma empresa

    **Retorna:**
    - `product_id`: ID do produto
    - `product_name`: Nome do produto
    - `cost_price`: Preço de custo
    - `sale_price`: Preço de venda normal
    - `promotional_price`: Preço promocional (se aplicável)
    - `is_on_sale`: Se está em promoção
    - `normal_profit`: Lucro com preço normal (sale_price - cost_price)
    - `normal_margin_percentage`: Margem % com preço normal
    - `promotional_profit`: Lucro com preço promocional (se aplicável)
    - `promotional_margin_percentage`: Margem % com preço promocional (se aplicável)
    - `active_profit`: Lucro atual considerando se está em promoção
    - `active_margin_percentage`: Margem % atual

    **Fórmulas:**
    - Lucro = Preço de Venda - Preço de Custo
    - Margem % = (Lucro / Preço de Venda) × 100

    **Exemplo:** GET /products/123/profit-analysis
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

    # Converter para float para cálculos
    cost_price = float(product.cost_price)
    sale_price = float(product.sale_price)
    promotional_price = float(product.promotional_price) if product.promotional_price else None

    # Calcular lucro e margem com preço normal
    normal_profit = sale_price - cost_price
    normal_margin_percentage = (normal_profit / sale_price * 100) if sale_price > 0 else 0.0

    # Calcular lucro e margem com preço promocional (se aplicável)
    promotional_profit = None
    promotional_margin_percentage = None

    if promotional_price is not None:
        promotional_profit = promotional_price - cost_price
        promotional_margin_percentage = (promotional_profit / promotional_price * 100) if promotional_price > 0 else 0.0

    # Determinar lucro e margem ativos (considerando se está em promoção)
    if product.is_on_sale and promotional_price is not None:
        active_profit = promotional_profit
        active_margin_percentage = promotional_margin_percentage
        active_price = promotional_price
    else:
        active_profit = normal_profit
        active_margin_percentage = normal_margin_percentage
        active_price = sale_price

    return {
        "product_id": product.id,
        "product_name": product.name,
        "cost_price": round(cost_price, 2),
        "sale_price": round(sale_price, 2),
        "promotional_price": round(promotional_price, 2) if promotional_price is not None else None,
        "is_on_sale": product.is_on_sale,
        "normal_profit": round(normal_profit, 2),
        "normal_margin_percentage": round(normal_margin_percentage, 2),
        "promotional_profit": round(promotional_profit, 2) if promotional_profit is not None else None,
        "promotional_margin_percentage": round(promotional_margin_percentage, 2) if promotional_margin_percentage is not None else None,
        "active_profit": round(active_profit, 2),
        "active_margin_percentage": round(active_margin_percentage, 2),
        "active_price": round(active_price, 2),
        "recommendation": (
            "⚠️ ATENÇÃO: Margem promocional muito baixa!" if product.is_on_sale and promotional_margin_percentage is not None and promotional_margin_percentage < 10
            else "✅ Margem saudável" if active_margin_percentage >= 20
            else "⚠️ Margem baixa - considere revisar precificação" if active_margin_percentage < 15
            else "📊 Margem aceitável"
        )
    }


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


@router.get("/by-category/{category_id}", summary="Produtos por categoria")
def get_products_by_category(
        category_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        active_only: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Produtos por Categoria**

    Lista produtos de uma categoria específica.

    **Isolamento:** Apenas produtos da mesma empresa
    
    **Parâmetros:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    - `active_only`: Se True, retorna apenas produtos ativos (padrão: False)
    """
    query = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.category_id == category_id
    )

    if active_only:
        query = query.filter(Product.is_active == True)

    total = query.count()

    if limit is None:
        limit = total if total > 0 else 1
        products = query.offset(skip).all()
    else:
        if limit > 200:
            limit = 200
        products = query.offset(skip).limit(limit).all()

    return [ProductResponse.model_validate(p).model_dump() for p in products]
