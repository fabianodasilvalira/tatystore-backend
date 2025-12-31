-- Migração Manual: Adicionar Constraints de Estoque
-- ATENÇÃO: Executar APENAS em desenvolvimento local, NÃO em produção!

-- 1. Verificar se há produtos com estoque negativo
SELECT id, name, sku, stock_quantity, min_stock
FROM products
WHERE stock_quantity < 0 OR min_stock < 0;

-- 2. Corrigir produtos com estoque negativo (se houver)
UPDATE products SET stock_quantity = 0 WHERE stock_quantity < 0;
UPDATE products SET min_stock = 0 WHERE min_stock < 0;

-- 3. Adicionar constraint para stock_quantity
ALTER TABLE products
ADD CONSTRAINT check_stock_non_negative CHECK (stock_quantity >= 0);

-- 4. Adicionar constraint para min_stock
ALTER TABLE products
ADD CONSTRAINT check_min_stock_non_negative CHECK (min_stock >= 0);

-- Verificar constraints criados
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'products'::regclass
AND conname LIKE 'check_%';
