"""
Script de verificação final dos testes
Valida que todos os 166 testes passam
"""
import subprocess
import sys
from datetime import datetime

def run_tests():
    """Executar todos os testes e exibir relatório"""
    print("=" * 80)
    print("VERIFICAÇÃO FINAL DE TESTES")
    print("=" * 80)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Executar pytest
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short"],
        capture_output=False,
        text=True
    )
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 80)
        return 0
    else:
        print("✗ ALGUNS TESTES FALHARAM")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
