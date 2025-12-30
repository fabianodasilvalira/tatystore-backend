-- Script para adicionar a coluna brand à tabela products
-- Este script corrige o erro: column products.brand does not exist

-- Adiciona a coluna brand se ela não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'brand'
    ) THEN
        ALTER TABLE products ADD COLUMN brand VARCHAR(100);
        RAISE NOTICE 'Coluna brand adicionada com sucesso!';
    ELSE
        RAISE NOTICE 'Coluna brand já existe!';
    END IF;
END $$;

-- Adiciona a coluna image_url se ela não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'image_url'
    ) THEN
        ALTER TABLE products ADD COLUMN image_url VARCHAR(500);
        RAISE NOTICE 'Coluna image_url adicionada com sucesso!';
    ELSE
        RAISE NOTICE 'Coluna image_url já existe!';
    END IF;
END $$;

-- Verifica as colunas da tabela products
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'products'
ORDER BY ordinal_position;
