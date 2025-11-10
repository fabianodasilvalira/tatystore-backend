"""
Script para análise completa da cobertura de testes
Identifica gaps e recomenda novos testes
"""
import subprocess
import json
import sys
from pathlib import Path
from collections import defaultdict

def run_tests_with_coverage():
    """Executa testes com cobertura"""
    print("[ANALYSIS] Executando testes com cobertura...")
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    return result

def parse_test_results(output):
    """Parse dos resultados de testes"""
    tests = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})
    
    for line in output.split('\n'):
        if 'PASSED' in line:
            module = line.split('::')[0].split('/')[-1].replace('.py', '')
            tests[module]["passed"] += 1
        elif 'FAILED' in line:
            module = line.split('::')[0].split('/')[-1].replace('.py', '')
            tests[module]["failed"] += 1
        elif 'SKIPPED' in line:
            module = line.split('::')[0].split('/')[-1].replace('.py', '')
            tests[module]["skipped"] += 1
    
    return tests

def generate_report(result):
    """Gera relatório de análise"""
    print("\n" + "="*80)
    print("RELATÓRIO DE ANÁLISE DE TESTES")
    print("="*80 + "\n")
    
    # Parse results
    tests = parse_test_results(result.stdout)
    
    # Summary
    total_passed = sum(t["passed"] for t in tests.values())
    total_failed = sum(t["failed"] for t in tests.values())
    total_skipped = sum(t["skipped"] for t in tests.values())
    
    print(f"RESUMO GERAL:")
    print(f"  ✓ Testes Aprovados: {total_passed}")
    print(f"  ✗ Testes Falhados: {total_failed}")
    print(f"  ⊘ Testes Ignorados: {total_skipped}")
    print(f"  Total: {total_passed + total_failed + total_skipped}\n")
    
    # Per module
    print("COBERTURA POR MÓDULO:")
    for module in sorted(tests.keys()):
        t = tests[module]
        total = t["passed"] + t["failed"] + t["skipped"]
        rate = (t["passed"] / total * 100) if total > 0 else 0
        status = "✓" if t["failed"] == 0 else "✗"
        print(f"  {status} {module}: {t['passed']}/{total} ({rate:.1f}%)")
    
    print("\n" + "="*80)
    print("ÁREAS DE COBERTURA DETECTADAS:")
    print("="*80 + "\n")
    
    areas = {
        "test_auth.py": "Autenticação e autorização",
        "test_companies.py": "Gestão de empresas",
        "test_products.py": "Gestão de produtos",
        "test_sales.py": "Gestão de vendas",
        "test_installments.py": "Gestão de parcelas",
        "test_reports.py": "Relatórios",
        "test_security.py": "Segurança e validação",
        "test_multi_tenant.py": "Multi-tenancy",
        "test_edge_cases.py": "Casos extremos",
        "test_company_flow.py": "Fluxos de negócio",
        "test_cron.py": "Agendamentos",
        "test_public.py": "Endpoints públicos"
    }
    
    for module, description in areas.items():
        if module in tests:
            status = "✓" if tests[module]["failed"] == 0 else "✗"
            print(f"{status} {description}: {module}")
    
    print("\n" + "="*80)
    print("RECOMENDAÇÕES DE NOVOS TESTES:")
    print("="*80 + "\n")
    
    recommendations = [
        ("Testes de concorrência", "Validar que múltiplas requisições simultâneas não causam race conditions"),
        ("Testes de integração API", "Fluxos completos end-to-end com múltiplas operações"),
        ("Testes de performance", "Validar tempos de resposta em grandes volumes de dados"),
        ("Testes de cache", "Validar que cache funciona corretamente em reports"),
        ("Testes de paginação", "Validar offset/limit em todos os endpoints de listagem"),
        ("Testes de filtros", "Validar todos os filtros disponíveis nos endpoints"),
        ("Testes de ordering", "Validar sorting em todas as listagens"),
        ("Testes de erro 500", "Validar tratamento de erros não esperados"),
        ("Testes de database", "Validar constraints e integridade referencial"),
        ("Testes de webhooks", "Se houver integração com webhooks externos")
    ]
    
    for i, (test_type, description) in enumerate(recommendations, 1):
        print(f"{i}. {test_type}")
        print(f"   → {description}\n")
    
    print("="*80 + "\n")
    
    # Exit code
    if total_failed > 0:
        print(f"❌ FALHA: {total_failed} testes falharam")
        return 1
    else:
        print("✅ SUCESSO: Todos os testes passaram!")
        return 0

if __name__ == "__main__":
    result = run_tests_with_coverage()
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    sys.exit(generate_report(result))
