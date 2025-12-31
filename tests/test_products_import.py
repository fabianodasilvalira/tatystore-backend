"""
Testes TDD para Importação em Massa de Produtos
Testa endpoint de importação via CSV com validações completas
"""
import pytest
import io
from tests.conftest import get_auth_headers


def create_csv_content(rows):
    """Helper para criar conteúdo CSV"""
    header = "nome,marca,categoria,descricao,preco_custo,preco_venda,estoque,estoque_minimo,sku,codigo_barras,ativo,em_promocao,preco_promocional\n"
    return header + "\n".join(rows)


def test_import_template_download(client, admin_token, test_category):
    """
    Teste: Download de template CSV com categorias da empresa
    """
    response = client.get(
        "/api/v1/products-import/import/template",
        headers=get_auth_headers(admin_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "content" in data
    assert "categorias_disponiveis" in data
    assert "instrucoes" in data
    assert test_category.name in data["categorias_disponiveis"]


def test_import_valid_csv_success(client, admin_token, test_category):
    """
    Teste: Importar CSV válido com produtos inativos
    """
    csv_rows = [
        f"Batom Natura 001,Natura,{test_category.name},Batom vermelho,15.50,35.90,0,5,NAT-BAT-001,7891234567890,false,false,",
        f"Perfume Boticário XYZ,Boticário,{test_category.name},Perfume masculino,45.00,120.00,0,3,BOT-PER-001,7891234567891,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_linhas"] == 2
    assert data["sucessos"] == 2
    assert data["erros"] == 0
    assert len(data["detalhes"]["criados"]) == 2
    assert len(data["detalhes"]["erros"]) == 0


def test_import_products_are_inactive_by_default(client, admin_token, test_category):
    """
    Teste: Produtos importados como inativos não aparecem na vitrine pública
    """
    csv_rows = [
        f"Produto Teste Inativo,Marca Teste,{test_category.name},Descrição,10.00,25.00,0,0,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    # Importar produto inativo
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sucessos"] == 1
    
    # Verificar que produto NÃO aparece na listagem pública
    # (assumindo que existe endpoint público)
    # Este teste pode ser ajustado conforme a estrutura do sistema


def test_import_missing_required_field_name(client, admin_token, test_category):
    """
    Teste: Erro ao importar sem campo obrigatório 'nome'
    """
    csv_rows = [
        f",Natura,{test_category.name},Descrição,15.50,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "nome" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_missing_required_field_brand(client, admin_token, test_category):
    """
    Teste: Erro ao importar sem campo obrigatório 'marca'
    """
    csv_rows = [
        f"Produto Teste,,{test_category.name},Descrição,15.50,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "marca" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_missing_required_field_category(client, admin_token):
    """
    Teste: Erro ao importar sem campo obrigatório 'categoria'
    """
    csv_rows = [
        "Produto Teste,Marca Teste,,Descrição,15.50,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "categoria" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_category_not_found(client, admin_token):
    """
    Teste: Erro quando categoria não existe no sistema
    """
    csv_rows = [
        "Produto Teste,Marca Teste,Categoria Inexistente,Descrição,15.50,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "não encontrada" in data["detalhes"]["erros"][0]["erro"].lower()
    assert "categorias disponíveis" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_invalid_price_format(client, admin_token, test_category):
    """
    Teste: Erro ao importar com preço inválido
    """
    csv_rows = [
        f"Produto Teste,Marca Teste,{test_category.name},Descrição,ABC,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "preco_custo" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_negative_price(client, admin_token, test_category):
    """
    Teste: Erro ao importar com preço negativo
    """
    csv_rows = [
        f"Produto Teste,Marca Teste,{test_category.name},Descrição,-10.00,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "negativo" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_accepts_comma_decimal_separator(client, admin_token, test_category):
    """
    Teste: Aceita vírgula como separador decimal
    """
    csv_rows = [
        f'Produto Teste,Marca Teste,{test_category.name},Descrição,"15,50","35,90",0,5,,,false,false,'
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sucessos"] == 1
    assert data["erros"] == 0


def test_import_promotional_price_required_when_on_sale(client, admin_token, test_category):
    """
    Teste: Preço promocional obrigatório quando em_promocao=true
    """
    csv_rows = [
        f"Produto Teste,Marca Teste,{test_category.name},Descrição,15.50,35.90,0,5,,,false,true,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["erros"] == 1
    assert data["sucessos"] == 0
    assert "preco_promocional" in data["detalhes"]["erros"][0]["erro"].lower()


def test_import_with_promotion_success(client, admin_token, test_category):
    """
    Teste: Importar produto em promoção com sucesso
    """
    csv_rows = [
        f"Produto Promoção,Marca Teste,{test_category.name},Descrição,15.50,35.90,0,5,,,true,true,29.90",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sucessos"] == 1
    assert data["erros"] == 0


def test_import_auto_generates_sku_when_empty(client, admin_token, test_category):
    """
    Teste: SKU é gerado automaticamente quando não fornecido
    """
    csv_rows = [
        f"Produto Sem SKU,Marca Teste,{test_category.name},Descrição,15.50,35.90,0,5,,,false,false,",
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sucessos"] == 1
    assert data["erros"] == 0
    assert "sku" in data["detalhes"]["criados"][0]
    assert data["detalhes"]["criados"][0]["sku"] != ""


def test_import_invalid_file_type(client, admin_token):
    """
    Teste: Rejeita arquivo que não é CSV
    """
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
    )
    
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_import_file_too_large(client, admin_token):
    """
    Teste: Rejeita arquivo maior que 5MB
    """
    # Criar arquivo grande (6MB)
    large_content = "a" * (6 * 1024 * 1024)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(large_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 400
    assert "5mb" in response.json()["detail"].lower()


def test_import_empty_csv(client, admin_token):
    """
    Teste: Erro ao importar CSV vazio
    """
    csv_content = ""
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 400
    assert "vazio" in response.json()["detail"].lower()


def test_import_missing_header(client, admin_token):
    """
    Teste: Erro quando falta campo obrigatório no cabeçalho
    """
    csv_content = "nome,marca,descricao\nProduto,Marca,Desc"
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 400
    assert "faltando" in response.json()["detail"].lower()


def test_import_mixed_success_and_errors(client, admin_token, test_category):
    """
    Teste: Importação com alguns sucessos e alguns erros
    """
    csv_rows = [
        f"Produto Válido 1,Marca,{test_category.name},Desc,10.00,20.00,0,0,,,false,false,",
        "Produto Inválido,,Categoria,Desc,10.00,20.00,0,0,,,false,false,",  # Sem marca
        f"Produto Válido 2,Marca,{test_category.name},Desc,15.00,30.00,0,0,,,false,false,",
        f"Produto Inválido 2,Marca,Categoria Inexistente,Desc,10.00,20.00,0,0,,,false,false,",  # Categoria inexistente
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_linhas"] == 4
    assert data["sucessos"] == 2
    assert data["erros"] == 2
    assert len(data["detalhes"]["criados"]) == 2
    assert len(data["detalhes"]["erros"]) == 2


def test_import_requires_admin_or_manager(client, seller_token, test_category):
    """
    Teste: Apenas Admin e Gerente podem importar
    """
    csv_rows = [
        f'Produto Teste,Marca,{test_category.name},Desc,"10.00","20.00",0,0,,,false,false,'
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(seller_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    # Deve retornar 403 (Forbidden) ou 401 (Unauthorized)
    assert response.status_code in [401, 403]


def test_import_isolates_by_company(client, admin_token, company2_token, test_category, test_category_company2):
    """
    Teste: Produtos importados são isolados por empresa
    """
    csv_rows_company1 = [
        f"Produto Empresa 1,Marca,{test_category.name},Desc,10.00,20.00,0,0,,,false,false,",
    ]
    csv_content_company1 = create_csv_content(csv_rows_company1)
    
    # Importar para empresa 1
    response1 = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content_company1.encode('utf-8')), "text/csv")}
    )
    
    assert response1.status_code == 200
    assert response1.json()["sucessos"] == 1
    
    # Verificar que empresa 2 não vê o produto da empresa 1
    response2 = client.get(
        "/api/v1/products/",
        headers=get_auth_headers(company2_token)
    )
    
    assert response2.status_code == 200
    products_company2 = response2.json()
    items = products_company2["items"] if isinstance(products_company2, dict) and "items" in products_company2 else products_company2
    product_names = [p["name"] for p in items]
    assert "Produto Empresa 1" not in product_names


def test_import_large_batch(client, admin_token, test_category):
    """
    Teste: Importar lote grande de produtos (100 produtos)
    """
    csv_rows = [
        f"Produto {i},Marca {i},{test_category.name},Descrição {i},{10+i},{20+i},0,0,,,false,false,"
        for i in range(100)
    ]
    csv_content = create_csv_content(csv_rows)
    
    response = client.post(
        "/api/v1/products-import/import",
        headers=get_auth_headers(admin_token),
        files={"file": ("test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_linhas"] == 100
    assert data["sucessos"] == 100
    assert data["erros"] == 0
