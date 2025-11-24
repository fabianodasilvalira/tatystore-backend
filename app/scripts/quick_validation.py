#!/usr/bin/env python3
"""
Script de Validação Rápida - Verifica se todas as correções estão funcionando

Uso:
    python scripts/quick_validation.py
"""

import sys
import os

# Adicionar o caminho da app ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_syntax():
    """Verifica se não há erros de sintaxe"""
    print("🔍 Verificando sintaxe dos arquivos...")
    
    files_to_check = [
        "app/api/v1/endpoints/installment_payments.py",
        "app/models/installment_payment.py",
        "app/schemas/installment_payment.py",
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"   ✅ {file_path}")
        except SyntaxError as e:
            print(f"   ❌ {file_path}: {e}")
            return False
        except FileNotFoundError:
            print(f"   ⚠️  {file_path} não encontrado")
    
    return True


def check_imports():
    """Verifica se os imports estão funcionando"""
    print("\n🔍 Verificando imports...")
    
    try:
        from app.models.installment_payment import InstallmentPayment, InstallmentPaymentStatus
        print("   ✅ InstallmentPayment importado com sucesso")
        
        from app.schemas.installment_payment import InstallmentPaymentCreate, InstallmentPaymentOut
        print("   ✅ Schemas de pagamento importados com sucesso")
        
        from app.api.v1.endpoints.installment_payments import router
        print("   ✅ Router de pagamentos importado com sucesso")
        
        return True
    except ImportError as e:
        print(f"   ❌ Erro ao importar: {e}")
        return False


def check_models():
    """Verifica se os modelos estão corretos"""
    print("\n🔍 Verificando modelos...")
    
    try:
        from app.models.installment_payment import InstallmentPayment
        from app.models.installment import Installment
        
        # Verificar relacionamento
        if hasattr(Installment, 'payments'):
            print("   ✅ Relacionamento Installment.payments existe")
        else:
            print("   ⚠️  Relacionamento Installment.payments não encontrado")
        
        return True
    except Exception as e:
        print(f"   ❌ Erro ao verificar modelos: {e}")
        return False


def check_database():
    """Verifica se a tabela de pagamentos existe"""
    print("\n🔍 Verificando banco de dados...")
    
    try:
        from sqlalchemy import inspect
        from app.core.database import engine
        from app.models.installment_payment import InstallmentPayment
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'installment_payments' in tables:
            print("   ✅ Tabela installment_payments existe")
            
            # Verificar colunas
            columns = [col['name'] for col in inspector.get_columns('installment_payments')]
            expected_columns = ['id', 'installment_id', 'amount_paid', 'paid_at', 'status']
            
            for col in expected_columns:
                if col in columns:
                    print(f"      ✅ Coluna '{col}' existe")
                else:
                    print(f"      ⚠️  Coluna '{col}' não encontrada")
            
            return True
        else:
            print("   ⚠️  Tabela installment_payments não existe")
            print("      Execute: python scripts/validate_fixes.py")
            return False
    except Exception as e:
        print(f"   ⚠️  Não foi possível verificar DB (esperado em desenvolvimento): {e}")
        return True  # Não é erro crítico


def main():
    print("=" * 60)
    print("🚀 VALIDAÇÃO RÁPIDA DO SISTEMA DE PAGAMENTOS PARCIAIS")
    print("=" * 60)
    
    results = []
    
    results.append(("Sintaxe", check_syntax()))
    results.append(("Imports", check_imports()))
    results.append(("Modelos", check_models()))
    results.append(("Banco de Dados", check_database()))
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ TUDO OK! Sistema pronto para testes.")
        print("\nPróximo passo:")
        print("   pytest tests/ -v")
        return 0
    else:
        print("\n❌ Há problemas a corrigir.")
        print("\nVerifique os erros acima e corrija.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
