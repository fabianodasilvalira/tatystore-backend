-- Migração para converter datas históricos de UTC para Fortaleza
-- Este script converte todos os datetimes salvos em UTC para o horário de Fortaleza (UTC-3)
-- Execução: Apenas execute se os dados foram salvos em UTC previamente

-- Fórmula: Adicionar 3 horas ao datetime UTC para converter para Fortaleza
-- Nota: Isso assume que as datas foram salvas como UTC naive (sem timezone info)

-- Atualizar installment_payments
UPDATE installment_payments 
SET 
    paid_at = DATE_ADD(paid_at, INTERVAL 3 HOUR),
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE paid_at IS NOT NULL;

-- Atualizar installments
UPDATE installments 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar sales
UPDATE sales 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar customers
UPDATE customers 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar companies
UPDATE companies 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar products
UPDATE products 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar categories
UPDATE categories 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar users
UPDATE users 
SET 
    created_at = DATE_ADD(created_at, INTERVAL 3 HOUR),
    updated_at = DATE_ADD(updated_at, INTERVAL 3 HOUR)
WHERE created_at IS NOT NULL;

-- Atualizar token_blacklist
UPDATE token_blacklist 
SET 
    revoked_at = DATE_ADD(revoked_at, INTERVAL 3 HOUR)
WHERE revoked_at IS NOT NULL;
