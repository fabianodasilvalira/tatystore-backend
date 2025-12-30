#!/usr/bin/env python3
"""
Script Python para executar testes específicos de pagamentos parciais
Uso: python scripts/run_partial_payments_tests.py [opção]
"""
import sys
import subprocess
import os

# Cores ANSI
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_header():
    print("=" * 60)
    print("TESTES DE PAGAMENTOS PARCIAIS - Sistema FastAPI")
    print("=" * 60)
    print()

def print_status(msg):
    print(f"{BLUE}[INFO]{NC} {msg}")

def print_success(msg):
    print(f"{GREEN}[OK]{NC} {msg}")

def print_error(msg):
    print(f"{RED}[ERRO]{NC} {msg}")

def run_pytest(args):
    """Executa pytest com os argumentos fornecidos"""
    cmd = ["pytest"] + args
    print_status(f"Executando: {' '.join(cmd)}")
    print()
    result = subprocess.run(cmd)
    return result.returncode

def main():
    print_header()
    
    # Verificar se pytest está instalado
    try:
        subprocess.run(["pytest", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("pytest não está instalado!")
        print_status("Instale com: pip install pytest pytest-cov")
        return 1
    
    # Arquivo de teste principal
    test_file = "tests/test_partial_payments_complete.py"
    
    # Processar opção
    option = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    test_commands = {
        "all": {
            "desc": "Todos os testes de pagamentos parciais",
            "args": [test_file, "-v"]
        },
        "metade": {
            "desc": "Testes de pagamento pela metade",
            "args": [f"{test_file}::TestPagamentoPorMetade", "-v"]
        },
        "qualquer-valor": {
            "desc": "Testes de pagamento por qualquer valor",
            "args": [f"{test_file}::TestPagamentoPorQualquerValor", "-v"]
        },
        "validacoes": {
            "desc": "Testes de validações e limites",
            "args": [f"{test_file}::TestValidacoesPagamentoParcial", "-v"]
        },
        "listagem": {
            "desc": "Testes de listagem com saldos",
            "args": [f"{test_file}::TestListagemComPagamentosParciais", "-v"]
        },
        "historico": {
            "desc": "Testes de histórico de pagamentos",
            "args": [f"{test_file}::TestHistoricoPagamentos", "-v"]
        },
        "praticos": {
            "desc": "Testes de cenários práticos",
            "args": [f"{test_file}::TestCenariosPraticos", "-v"]
        },
        "coverage": {
            "desc": "Todos os testes com cobertura de código",
            "args": [
                test_file,
                "--cov=api/v1/endpoints/installments",
                "--cov=api/v1/endpoints/installment_payments",
                "--cov-report=html",
                "--cov-report=term-missing",
                "-v"
            ]
        },
        "debug": {
            "desc": "Modo debug com output completo",
            "args": [test_file, "-v", "-s", "--tb=long"]
        },
        "fast": {
            "desc": "Execução rápida (para na primeira falha)",
            "args": [test_file, "-v", "-x"]
        }
    }
    
    if option == "help" or option not in test_commands:
        print("Uso: python scripts/run_partial_payments_tests.py [opção]")
        print()
        print("Opções disponíveis:")
        print()
        for cmd, info in test_commands.items():
            print(f"  {cmd:20} - {info['desc']}")
        print()
        print("Exemplos:")
        print("  python scripts/run_partial_payments_tests.py all")
        print("  python scripts/run_partial_payments_tests.py metade")
        print("  python scripts/run_partial_payments_tests.py coverage")
        print()
        return 0 if option == "help" else 1
    
    # Executar testes
    cmd_info = test_commands[option]
    print_status(cmd_info["desc"])
    print()
    
    returncode = run_pytest(cmd_info["args"])
    
    print()
    if returncode == 0:
        print_success("Testes completados com sucesso!")
    else:
        print_error("Alguns testes falharam!")
    
    return returncode

if __name__ == "__main__":
    sys.exit(main())
