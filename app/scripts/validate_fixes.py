"""
Script para validar que todos os bugs foram corrigidos
Executa cenários críticos que estavam falhando antes
"""
import subprocess
import sys
from typing import List, Tuple

class TestValidator:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests: List[Tuple[str, str]] = []
    
    def add_test(self, name: str, command: str):
        """Adiciona um teste crítico para validar"""
        self.tests.append((name, command))
    
    def run(self) -> bool:
        """Executa todos os testes críticos"""
        print("=" * 60)
        print("VALIDADOR DE CORREÇÕES - PAGAMENTOS PARCIAIS")
        print("=" * 60)
        print()
        
        for name, command in self.tests:
            print(f"Validando: {name}")
            print(f"Comando: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ PASSOU\n")
                self.passed += 1
            else:
                print(f"✗ FALHOU")
                print(f"Erro: {result.stderr}\n")
                self.failed += 1
        
        # Resumo
        print("=" * 60)
        print(f"Resultados: {self.passed} passou, {self.failed} falhou")
        print("=" * 60)
        
        return self.failed == 0


def main():
    validator = TestValidator()
    
    # TESTES CRÍTICOS que validam as correções
    
    # 1. BUG CRÍTICO: Débito total incorreto
    validator.add_test(
        "BUG #1: Débito total com pagamento parcial",
        "pytest tests/test_customer_total_debt.py::TestCustomerTotalDebt::test_total_debt_com_pagamento_parcial_uma_parcela -v"
    )
    
    # 2. Múltiplos pagamentos parciais
    validator.add_test(
        "BUG #2: Débito total com múltiplos pagamentos",
        "pytest tests/test_customer_total_debt.py::TestCustomerTotalDebt::test_total_debt_multiplos_pagamentos_parciais -v"
    )
    
    # 3. Saldos em listagens
    validator.add_test(
        "BUG #3: Saldos não aparecem em listagens",
        "pytest tests/test_installment_list_balances.py::TestInstallmentListWithBalances::test_listar_todas_parcelas_com_saldos -v"
    )
    
    # 4. Relatório de vencidas
    validator.add_test(
        "BUG #4: Relatório de vencidas com saldos incorretos",
        "pytest tests/test_reports_corrections.py::TestReportOverdueInstallments::test_report_overdue_com_saldos_corretos -v"
    )
    
    # 5. Relatório de resumo
    validator.add_test(
        "BUG #5: Resumo de vendas incorreto",
        "pytest tests/test_reports_corrections.py::TestReportSalesSummary::test_report_sales_summary_com_pagamentos_parciais -v"
    )
    
    # 6. Cron jobs não quebram
    validator.add_test(
        "BUG #6: Cron jobs com pagamentos parciais",
        "pytest tests/test_cron_jobs.py::TestMarkOverdueInstallments::test_marcar_vencida_com_pagamento_parcial -v"
    )
    
    # 7. Criação de pagamentos
    validator.add_test(
        "FEATURE: Criar pagamentos parciais",
        "pytest tests/test_installment_payments.py::TestInstallmentPaymentCreation::test_criar_pagamento_parcial_sucesso -v"
    )
    
    # Executar validação
    success = validator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
