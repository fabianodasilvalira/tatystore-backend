"""
Endpoint de Importação em Massa de Produtos
Permite importar centenas de produtos via arquivo CSV
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import csv
import io
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.api.v1.endpoints.products import generate_sku

router = APIRouter()


def parse_bool(value: str) -> bool:
    """Converte string para boolean"""
    if not value or value.strip() == '':
        return False
    return value.lower() in ('true', 'sim', 'yes', '1', 't', 's', 'y')


def parse_float(value: str, field_name: str, line_number: int) -> float:
    """Converte string para float com validação"""
    if not value or value.strip() == '':
        raise ValueError(f"Linha {line_number}: Campo '{field_name}' é obrigatório")
    
    try:
        # Aceita tanto vírgula quanto ponto como separador decimal
        value_clean = value.replace(',', '.')
        result = float(value_clean)
        if result < 0:
            raise ValueError(f"Linha {line_number}: '{field_name}' não pode ser negativo")
        return result
    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError(f"Linha {line_number}: '{field_name}' deve ser um número válido")
        raise


def parse_int(value: str, field_name: str, line_number: int, default: int = 0) -> int:
    """Converte string para int com validação"""
    if not value or value.strip() == '':
        return default
    
    try:
        result = int(value)
        if result < 0:
            raise ValueError(f"Linha {line_number}: '{field_name}' não pode ser negativo")
        return result
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Linha {line_number}: '{field_name}' deve ser um número inteiro válido")
        raise


@router.post("/import", summary="Importar produtos em massa via CSV")
async def import_products(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Importar Produtos em Massa via CSV**
    
    Permite importar centenas de produtos de uma vez via arquivo CSV.
    
    **Requer:** Admin ou Gerente
    """
    
    # Validar tipo de arquivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos CSV são permitidos"
        )
    
    # Validar tamanho (5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo 5MB"
        )
    
    # Decodificar CSV
    try:
        csv_content = contents.decode('utf-8-sig')  # utf-8-sig remove BOM se presente
    except UnicodeDecodeError:
        try:
            csv_content = contents.decode('latin-1')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível decodificar o arquivo. Use UTF-8 ou Latin-1"
            )
    
    # Processar CSV
    csv_file = io.StringIO(csv_content)
    csv_reader = csv.DictReader(csv_file)
    
    # Validar cabeçalho
    required_fields = {'nome', 'marca', 'categoria', 'preco_custo', 'preco_venda'}
    if not csv_reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo CSV vazio ou sem cabeçalho"
        )
    
    header_fields = set(field.lower().strip() for field in csv_reader.fieldnames)
    missing_fields = required_fields - header_fields
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campos obrigatórios faltando no CSV: {', '.join(missing_fields)}"
        )
    
    # Buscar todas as categorias da empresa uma vez (otimização)
    categories = db.query(Category).filter(
        Category.company_id == current_user.company_id,
        Category.is_active == True
    ).all()
    category_map = {cat.name.lower().strip(): cat.id for cat in categories}
    
    # Processar linhas
    results = {
        "total_linhas": 0,
        "sucessos": 0,
        "erros": 0,
        "detalhes": {
            "criados": [],
            "erros": []
        }
    }
    
    line_number = 1  # Linha 1 é o cabeçalho
    
    for row in csv_reader:
        line_number += 1
        
        try:
            # Normalizar chaves do dicionário (lowercase e strip)
            row_normalized = {k.lower().strip(): v.strip() if v else '' for k, v in row.items()}
            
            # Validar campos obrigatórios
            if not row_normalized.get('nome'):
                raise ValueError(f"Linha {line_number}: Campo 'nome' é obrigatório")
            
            if not row_normalized.get('marca'):
                raise ValueError(f"Linha {line_number}: Campo 'marca' é obrigatório")
            
            if not row_normalized.get('categoria'):
                raise ValueError(f"Linha {line_number}: Campo 'categoria' é obrigatório")
            
            # Validar categoria existe
            category_name = row_normalized['categoria'].lower().strip()
            category_id = category_map.get(category_name)
            
            if not category_id:
                available_categories = ', '.join(sorted(set(cat.name for cat in categories)))
                raise ValueError(
                    f"Linha {line_number}: Categoria '{row_normalized['categoria']}' não encontrada. "
                    f"Categorias disponíveis: {available_categories}"
                )
            
            # Parse de valores
            preco_custo = parse_float(row_normalized.get('preco_custo', ''), 'preco_custo', line_number)
            preco_venda = parse_float(row_normalized.get('preco_venda', ''), 'preco_venda', line_number)
            estoque = parse_int(row_normalized.get('estoque', '0'), 'estoque', line_number, default=0)
            estoque_minimo = parse_int(row_normalized.get('estoque_minimo', '0'), 'estoque_minimo', line_number, default=0)
            ativo = parse_bool(row_normalized.get('ativo', 'false'))
            em_promocao = parse_bool(row_normalized.get('em_promocao', 'false'))
            
            # Validar preço promocional se em promoção
            preco_promocional = None
            if em_promocao:
                preco_promo_str = row_normalized.get('preco_promocional', '')
                if not preco_promo_str:
                    raise ValueError(f"Linha {line_number}: 'preco_promocional' é obrigatório quando 'em_promocao' é true")
                preco_promocional = parse_float(preco_promo_str, 'preco_promocional', line_number)
            
            # Gerar SKU se não fornecido
            sku = row_normalized.get('sku', '').strip()
            if not sku:
                sku = generate_sku(
                    db=db,
                    company_id=current_user.company_id,
                    product_name=row_normalized['nome'],
                    category_id=category_id
                )
            
            # Criar produto
            product = Product(
                name=row_normalized['nome'],
                brand=row_normalized['marca'],
                description=row_normalized.get('descricao', ''),
                category_id=category_id,
                cost_price=preco_custo,
                sale_price=preco_venda,
                stock_quantity=estoque,
                min_stock=estoque_minimo,
                sku=sku,
                barcode=row_normalized.get('codigo_barras', ''),
                is_active=ativo,
                is_on_sale=em_promocao,
                promotional_price=preco_promocional,
                company_id=current_user.company_id
            )
            
            db.add(product)
            results["sucessos"] += 1
            results["detalhes"]["criados"].append({
                "linha": line_number,
                "nome": row_normalized['nome'],
                "sku": sku
            })
            
        except ValueError as e:
            results["erros"] += 1
            results["detalhes"]["erros"].append({
                "linha": line_number,
                "erro": str(e)
            })
        except Exception as e:
            results["erros"] += 1
            results["detalhes"]["erros"].append({
                "linha": line_number,
                "erro": f"Erro inesperado: {str(e)}"
            })
    
    results["total_linhas"] = line_number - 1  # Excluir linha de cabeçalho
    
    # Commit apenas se houver sucessos
    if results["sucessos"] > 0:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar produtos no banco de dados: {str(e)}"
            )
    
    return results


@router.get("/import/template", summary="Download template CSV para importação")
async def download_template(
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Download Template CSV**
    
    Retorna um template CSV com exemplos para facilitar a importação.
    
    **Requer:** Admin ou Gerente
    """
    
    # Buscar categorias da empresa para incluir no exemplo
    categories = db.query(Category).filter(
        Category.company_id == current_user.company_id,
        Category.is_active == True
    ).limit(3).all()
    
    category_examples = [cat.name for cat in categories] if categories else ["Maquiagem", "Perfumaria", "Cuidados"]
    
    # Criar CSV de exemplo
    csv_content = "nome,marca,categoria,descricao,preco_custo,preco_venda,estoque,estoque_minimo,sku,codigo_barras,ativo,em_promocao,preco_promocional\n"
    csv_content += f"Batom Natura 001,Natura,{category_examples[0]},Batom vermelho intenso,15.50,35.90,0,5,NAT-BAT-001,7891234567890,false,false,\n"
    csv_content += f"Perfume Boticário XYZ,Boticário,{category_examples[1] if len(category_examples) > 1 else category_examples[0]},Perfume masculino 100ml,45.00,120.00,0,3,BOT-PER-001,7891234567891,false,false,\n"
    csv_content += f"Creme Eudora ABC,Eudora,{category_examples[2] if len(category_examples) > 2 else category_examples[0]},Creme hidratante facial,25.00,65.00,0,10,EUD-CRE-001,7891234567892,false,true,49.90\n"
    
    return {
        "filename": "template_importacao_produtos.csv",
        "content": csv_content,
        "categorias_disponiveis": [cat.name for cat in categories] if categories else [],
        "instrucoes": {
            "campos_obrigatorios": ["nome", "marca", "categoria", "preco_custo", "preco_venda"],
            "formato_preco": "Use ponto ou vírgula como separador decimal (ex: 15.50 ou 15,50)",
            "formato_booleano": "Use true/false, sim/não, 1/0 para campos ativo e em_promocao",
            "categoria": "Deve ser exatamente igual a uma categoria existente no sistema",
            "sku": "Deixe vazio para gerar automaticamente",
            "ativo": "Use 'false' para produtos que ainda precisam de ajuste de preço"
        }
    }
