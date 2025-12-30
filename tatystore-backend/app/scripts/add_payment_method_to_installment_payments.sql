-- Script de migração para adicionar coluna payment_method
-- Execute este script no banco de dados para adicionar a coluna faltante

-- Adicionar coluna payment_method à tabela installment_payments
ALTER TABLE installment_payments 
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'cash';

-- Atualizar registros existentes para ter método de pagamento padrão
UPDATE installment_payments 
SET payment_method = 'cash' 
WHERE payment_method IS NULL;

-- Adicionar comentário na coluna
COMMENT ON COLUMN installment_payments.payment_method IS 'Método de pagamento utilizado (cash, credit, pix)';
