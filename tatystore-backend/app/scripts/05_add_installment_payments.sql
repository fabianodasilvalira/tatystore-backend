-- =====================================================
-- MIGRATION: Adicionar suporte a pagamentos parciais de parcelas
-- =====================================================
-- Este script cria a tabela installment_payments para rastrear
-- pagamentos parciais de parcelas. Permite que um cliente pague
-- uma parcela em múltiplas transações.
-- =====================================================

-- Criar tabela de pagamentos de parcelas
CREATE TABLE IF NOT EXISTS installment_payments (
    id SERIAL PRIMARY KEY,
    installment_id INTEGER NOT NULL REFERENCES installments(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    amount_paid FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    paid_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_installment (installment_id),
    INDEX idx_company (company_id),
    INDEX idx_status (status)
);

-- Adicionar comentário descritivo
COMMENT ON TABLE installment_payments IS 'Registro de pagamentos parciais de parcelas. Uma parcela pode ter múltiplos registros.';
COMMENT ON COLUMN installment_payments.amount_paid IS 'Valor pago nesta transação específica';
COMMENT ON COLUMN installment_payments.status IS 'Status do pagamento: pending, completed, failed';

-- Criar índices de busca rápida
CREATE INDEX IF NOT EXISTS idx_installment_payments_date ON installment_payments(paid_at DESC);
CREATE INDEX IF NOT EXISTS idx_installment_payments_company_status ON installment_payments(company_id, status);
