"""
Testes para validação condicional de clientes em vendas a crediário

Este módulo testa:
1. Vendas à vista (PIX, dinheiro, cartão) aceitam clientes sem dados completos
2. Vendas a crediário exigem CPF, telefone e endereço
3. Mensagens de erro são específicas e claras
4. Validação funciona tanto no frontend quanto no backend
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.sale import PaymentMethod
from sqlalchemy.orm import Session

# Configuração de autenticação
BASE_URL = "http://localhost:8000/api/v1"
AUTH_EMAIL = "admin@tatystore.com"
AUTH_PASSWORD = "admin123"

def get_auth_token():
    """Obtém token de autenticação"""
    import urllib.request
    import urllib.error
    
    auth_data = json.dumps({
        "email": AUTH_EMAIL,
        "password": AUTH_PASSWORD
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=auth_data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['access_token']
    except urllib.error.HTTPError as e:
        print(f"❌ Erro ao autenticar: {e.code}")
        print(f"   Resposta: {e.read().decode('utf-8')}")
        raise

def create_test_customer(token: str, customer_data: dict) -> dict:
    """Cria um cliente de teste"""
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        f"{BASE_URL}/customers/",
        data=json.dumps(customer_data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"❌ Erro ao criar cliente: {e.code}")
        print(f"   Resposta: {error_msg}")
        raise Exception(f"Falha ao criar cliente: {error_msg}")

def create_test_sale(token: str, sale_data: dict) -> tuple:
    """
    Tenta criar uma venda de teste
    Retorna (sucesso: bool, resposta: dict, erro: str)
    """
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        f"{BASE_URL}/sales/",
        data=json.dumps(sale_data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return (True, result, None)
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        return (False, None, error_data.get('detail', 'Erro desconhecido'))

def get_test_product(db: Session) -> Product:
    """Obtém ou cria um produto de teste"""
    product = db.query(Product).filter(Product.name == "Produto Teste Validação").first()
    
    if not product:
        # Busca uma empresa ativa
        company = db.query(Company).filter(Company.is_active == True).first()
        if not company:
            raise Exception("Nenhuma empresa ativa encontrada")
        
        product = Product(
            name="Produto Teste Validação",
            description="Produto para testes de validação",
            sale_price=100.0,
            cost_price=50.0,
            stock_quantity=1000,
            company_id=company.id,
            is_active=True
        )
        db.add(product)
        db.commit()
        db.refresh(product)
    
    return product

def test_cash_sale_without_complete_data():
    """
    Teste 1: Venda à vista (dinheiro) deve aceitar cliente sem CPF, telefone e endereço
    """
    print("\n" + "="*80)
    print("TESTE 1: Venda à Vista com Cliente Incompleto")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente SEM CPF, telefone e endereço
        customer_data = {
            "name": f"Cliente Teste Cash {datetime.now().strftime('%H%M%S')}",
            "email": None,
            "phone": None,
            "cpf": None,
            "address": None,
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        print(f"  - CPF: {customer.get('cpf', 'Não informado')}")
        print(f"  - Telefone: {customer.get('phone', 'Não informado')}")
        print(f"  - Endereço: {customer.get('address', 'Não informado')}")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda à vista (CASH)
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "cash",
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if success:
            print(f"✅ PASSOU: Venda à vista aceita cliente sem dados completos")
            print(f"   Venda ID: {result['id']}")
            print(f"   Total: R$ {result['total_amount']:.2f}")
            return True
        else:
            print(f"❌ FALHOU: Venda à vista rejeitou cliente sem dados completos")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def test_pix_sale_without_complete_data():
    """
    Teste 2: Venda PIX deve aceitar cliente sem CPF, telefone e endereço
    """
    print("\n" + "="*80)
    print("TESTE 2: Venda PIX com Cliente Incompleto")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente SEM CPF, telefone e endereço
        customer_data = {
            "name": f"Cliente Teste PIX {datetime.now().strftime('%H%M%S')}",
            "email": None,
            "phone": None,
            "cpf": None,
            "address": None,
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda PIX
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "pix",
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if success:
            print(f"✅ PASSOU: Venda PIX aceita cliente sem dados completos")
            print(f"   Venda ID: {result['id']}")
            return True
        else:
            print(f"❌ FALHOU: Venda PIX rejeitou cliente sem dados completos")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def test_credit_sale_without_cpf():
    """
    Teste 3: Venda a crediário deve REJEITAR cliente sem CPF
    """
    print("\n" + "="*80)
    print("TESTE 3: Venda a Crediário SEM CPF (deve falhar)")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente SEM CPF (mas com telefone e endereço)
        customer_data = {
            "name": f"Cliente Teste Credit {datetime.now().strftime('%H%M%S')}",
            "email": None,
            "phone": "11999999999",
            "cpf": None,  # SEM CPF
            "address": "Rua Teste, 123",
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        print(f"  - CPF: {customer.get('cpf', 'NÃO INFORMADO')}")
        print(f"  - Telefone: {customer.get('phone', 'Não informado')}")
        print(f"  - Endereço: {customer.get('address', 'Não informado')}")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda a crediário
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "credit",
            "installments_count": 3,
            "first_due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if not success and "CPF" in error:
            print(f"✅ PASSOU: Venda a crediário rejeitou cliente sem CPF")
            print(f"   Mensagem de erro: {error}")
            return True
        elif success:
            print(f"❌ FALHOU: Venda a crediário ACEITOU cliente sem CPF")
            print(f"   Venda ID: {result['id']} (NÃO DEVERIA TER SIDO CRIADA)")
            return False
        else:
            print(f"⚠️  FALHOU: Erro diferente do esperado")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def test_credit_sale_without_phone():
    """
    Teste 4: Venda a crediário deve REJEITAR cliente sem telefone
    """
    print("\n" + "="*80)
    print("TESTE 4: Venda a Crediário SEM Telefone (deve falhar)")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente SEM telefone (mas com CPF e endereço)
        customer_data = {
            "name": f"Cliente Teste Credit {datetime.now().strftime('%H%M%S')}",
            "email": None,
            "phone": None,  # SEM TELEFONE
            "cpf": "12345678901",
            "address": "Rua Teste, 123",
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        print(f"  - CPF: {customer.get('cpf', 'Não informado')}")
        print(f"  - Telefone: {customer.get('phone', 'NÃO INFORMADO')}")
        print(f"  - Endereço: {customer.get('address', 'Não informado')}")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda a crediário
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "credit",
            "installments_count": 3,
            "first_due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if not success and "Telefone" in error:
            print(f"✅ PASSOU: Venda a crediário rejeitou cliente sem telefone")
            print(f"   Mensagem de erro: {error}")
            return True
        elif success:
            print(f"❌ FALHOU: Venda a crediário ACEITOU cliente sem telefone")
            return False
        else:
            print(f"⚠️  FALHOU: Erro diferente do esperado")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def test_credit_sale_without_address():
    """
    Teste 5: Venda a crediário deve REJEITAR cliente sem endereço
    """
    print("\n" + "="*80)
    print("TESTE 5: Venda a Crediário SEM Endereço (deve falhar)")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente SEM endereço (mas com CPF e telefone)
        customer_data = {
            "name": f"Cliente Teste Credit {datetime.now().strftime('%H%M%S')}",
            "email": None,
            "phone": "11999999999",
            "cpf": "12345678901",
            "address": None,  # SEM ENDEREÇO
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        print(f"  - CPF: {customer.get('cpf', 'Não informado')}")
        print(f"  - Telefone: {customer.get('phone', 'Não informado')}")
        print(f"  - Endereço: {customer.get('address', 'NÃO INFORMADO')}")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda a crediário
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "credit",
            "installments_count": 3,
            "first_due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if not success and "Endereço" in error:
            print(f"✅ PASSOU: Venda a crediário rejeitou cliente sem endereço")
            print(f"   Mensagem de erro: {error}")
            return True
        elif success:
            print(f"❌ FALHOU: Venda a crediário ACEITOU cliente sem endereço")
            return False
        else:
            print(f"⚠️  FALHOU: Erro diferente do esperado")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def test_credit_sale_with_complete_data():
    """
    Teste 6: Venda a crediário deve ACEITAR cliente com todos os dados
    """
    print("\n" + "="*80)
    print("TESTE 6: Venda a Crediário com Dados Completos (deve passar)")
    print("="*80)
    
    token = get_auth_token()
    db = SessionLocal()
    
    try:
        # Criar cliente COM todos os dados
        customer_data = {
            "name": f"Cliente Teste Credit Completo {datetime.now().strftime('%H%M%S')}",
            "email": "teste@email.com",
            "phone": "11999999999",
            "cpf": "12345678901",
            "address": "Rua Teste, 123, Bairro Teste, Cidade - UF",
            "is_active": True
        }
        
        customer = create_test_customer(token, customer_data)
        print(f"✓ Cliente criado: {customer['name']} (ID: {customer['id']})")
        print(f"  - CPF: {customer.get('cpf')}")
        print(f"  - Telefone: {customer.get('phone')}")
        print(f"  - Endereço: {customer.get('address')}")
        
        # Obter produto de teste
        product = get_test_product(db)
        
        # Tentar criar venda a crediário
        sale_data = {
            "customer_id": customer['id'],
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                    "unit_price": 100.0
                }
            ],
            "payment_type": "credit",
            "installments_count": 3,
            "first_due_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "discount_amount": 0
        }
        
        success, result, error = create_test_sale(token, sale_data)
        
        if success:
            print(f"✅ PASSOU: Venda a crediário aceita cliente com dados completos")
            print(f"   Venda ID: {result['id']}")
            print(f"   Total: R$ {result['total_amount']:.2f}")
            print(f"   Parcelas: {len(result.get('installments', []))}")
            return True
        else:
            print(f"❌ FALHOU: Venda a crediário rejeitou cliente com dados completos")
            print(f"   Erro: {error}")
            return False
            
    finally:
        db.close()

def run_all_tests():
    """Executa todos os testes e gera relatório"""
    print("\n" + "="*80)
    print("INICIANDO SUITE DE TESTES - VALIDAÇÃO CONDICIONAL DE CLIENTES")
    print("="*80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {BASE_URL}")
    
    tests = [
        ("Venda à Vista (Dinheiro) - Cliente Incompleto", test_cash_sale_without_complete_data),
        ("Venda PIX - Cliente Incompleto", test_pix_sale_without_complete_data),
        ("Venda a Crediário - SEM CPF", test_credit_sale_without_cpf),
        ("Venda a Crediário - SEM Telefone", test_credit_sale_without_phone),
        ("Venda a Crediário - SEM Endereço", test_credit_sale_without_address),
        ("Venda a Crediário - Dados Completos", test_credit_sale_with_complete_data),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO no teste '{test_name}': {str(e)}")
            results.append((test_name, False, str(e)))
    
    # Relatório Final
    print("\n" + "="*80)
    print("RELATÓRIO FINAL")
    print("="*80)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for test_name, passed, error in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if error:
            print(f"         Erro: {error}")
    
    print("\n" + "-"*80)
    print(f"Total: {passed_count}/{total_count} testes passaram ({(passed_count/total_count)*100:.1f}%)")
    print("="*80)
    
    return passed_count == total_count

if __name__ == "__main__":
    try:
        all_passed = run_all_tests()
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
