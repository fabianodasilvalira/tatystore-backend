-- Script para corrigir datas históricos salvos com timezone incorreto
-- Executa apenas UMA VEZ após fazer deploy das correções de código
-- 
-- IMPORTANTE: Backup do banco ANTES de executar este script!
-- 
-- A partir de agora:
-- - Banco salva todas as datas em UTC (via func.now())
-- - Python converte UTC para Fortaleza ao exibir (via serializers)
-- - Datas históricas serão convertidas por este script

-- Não fazer nada aqui - os dados históricos permanecerão em UTC
-- O frontend/serializers farão a conversão de UTC para Fortaleza
-- Isso garante que todas as datas sejam tratadas consistentemente

-- Se precisar verificar datas no banco, lembre-se que estão em UTC
-- SELECT created_at AT TIME ZONE 'America/Fortaleza' FROM installment_payments;
