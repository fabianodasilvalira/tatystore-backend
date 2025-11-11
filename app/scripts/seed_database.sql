-- =====================================================
-- SCRIPT ÚNICO DE SEED DO BANCO DE DADOS
-- =====================================================
-- Este script cria todos os dados necessários para testes:
-- - 2 empresas (taty e carol)
-- - 4 categorias por empresa
-- - 15 produtos por empresa (7 em promoção)
-- - 5 clientes por empresa
-- - Vendas de exemplo com diferentes tipos de pagamento
-- - Parcelas para crediário
-- =====================================================

-- Limpar dados existentes (ordem importante por causa das FKs)
TRUNCATE TABLE sale_items CASCADE;
TRUNCATE TABLE installments CASCADE;
TRUNCATE TABLE sales CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE categories CASCADE;
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE companies CASCADE;

-- =====================================================
-- EMPRESAS
-- =====================================================
INSERT INTO companies (id, name, slug, email, phone, cnpj, address, city, state, zip_code, is_active, created_at, updated_at)
VALUES 
  (1, 'Taty Perfumaria', 'taty', 'contato@tatyperfumaria.com', '11987654321', '12345678000190', 'Rua das Flores, 123', 'São Paulo', 'SP', '01234-567', true, NOW(), NOW()),
  (2, 'Carol Cosméticos', 'carol', 'contato@carolcosmeticos.com', '11987654322', '98765432000109', 'Av. Beleza, 456', 'Rio de Janeiro', 'RJ', '20000-000', true, NOW(), NOW());

-- =====================================================
-- USUÁRIOS (senha: senha123)
-- =====================================================
INSERT INTO users (id, email, password_hash, name, company_id, role, is_active, created_at, updated_at)
VALUES
  (1, 'admin@tatyperfumaria.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UPR7lWZ8WKPq', 'Admin Taty', 1, 'gerente', true, NOW(), NOW()),
  (2, 'vendedor@tatyperfumaria.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UPR7lWZ8WKPq', 'Vendedor Taty', 1, 'vendedor', true, NOW(), NOW()),
  (3, 'admin@carolcosmeticos.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UPR7lWZ8WKPq', 'Admin Carol', 2, 'gerente', true, NOW(), NOW()),
  (4, 'vendedor@carolcosmeticos.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UPR7lWZ8WKPq', 'Vendedor Carol', 2, 'vendedor', true, NOW(), NOW());

-- =====================================================
-- CATEGORIAS (4 por empresa)
-- =====================================================
INSERT INTO categories (id, name, description, company_id, is_active, created_at, updated_at)
VALUES
  -- Taty Perfumaria
  (1, 'Perfumes', 'Perfumes importados e nacionais', 1, true, NOW(), NOW()),
  (2, 'Cosméticos', 'Maquiagem e cosméticos diversos', 1, true, NOW(), NOW()),
  (3, 'Higiene Pessoal', 'Produtos de higiene e cuidados pessoais', 1, true, NOW(), NOW()),
  (4, 'Presentes & Kits', 'Kits e conjuntos para presente', 1, true, NOW(), NOW()),
  
  -- Carol Cosméticos
  (5, 'Perfumes', 'Perfumes importados e nacionais', 2, true, NOW(), NOW()),
  (6, 'Cosméticos', 'Maquiagem e cosméticos diversos', 2, true, NOW(), NOW()),
  (7, 'Higiene Pessoal', 'Produtos de higiene e cuidados pessoais', 2, true, NOW(), NOW()),
  (8, 'Presentes & Kits', 'Kits e conjuntos para presente', 2, true, NOW(), NOW());

-- =====================================================
-- PRODUTOS - TATY PERFUMARIA (15 produtos, 7 em promoção)
-- =====================================================
INSERT INTO products (id, name, description, sku, barcode, brand, sale_price, cost_price, stock_quantity, min_stock, category_id, is_on_sale, promotional_price, company_id, is_active, created_at, updated_at)
VALUES
  -- Perfumes (categoria 1)
  (1, 'Perfume Importado A', 'Fragrância floral com notas amadeiradas', 'PERF-001', '7891234567890', 'Marca A', 350.00, 200.00, 25, 5, 1, true, 299.90, 1, true, NOW(), NOW()),
  (2, 'Perfume Nacional B', 'Essência cítrica refrescante', 'PERF-002', '7891234567891', 'Marca B', 180.00, 100.00, 40, 10, 1, false, NULL, 1, true, NOW(), NOW()),
  (3, 'Perfume Premium C', 'Fragrância exclusiva oriental', 'PERF-003', '7891234567892', 'Marca C', 500.00, 280.00, 15, 5, 1, true, 449.90, 1, true, NOW(), NOW()),
  
  -- Cosméticos (categoria 2)
  (4, 'Base Líquida HD', 'Cobertura alta e acabamento natural', 'COS-001', '7891234567893', 'Makeup Pro', 85.00, 45.00, 50, 10, 2, true, 69.90, 1, true, NOW(), NOW()),
  (5, 'Batom Matte Vermelho', 'Longa duração e alta pigmentação', 'COS-002', '7891234567894', 'Makeup Pro', 45.00, 22.00, 80, 15, 2, false, NULL, 1, true, NOW(), NOW()),
  (6, 'Paleta de Sombras', '20 cores vibrantes e versáteis', 'COS-003', '7891234567895', 'ColorBeauty', 120.00, 60.00, 30, 8, 2, true, 99.90, 1, true, NOW(), NOW()),
  (7, 'Máscara para Cílios', 'Volume e alongamento extremo', 'COS-004', '7891234567896', 'LashMax', 65.00, 32.00, 45, 10, 2, false, NULL, 1, true, NOW(), NOW()),
  
  -- Higiene Pessoal (categoria 3)
  (8, 'Shampoo Hidratante 500ml', 'Hidratação profunda para todos os tipos de cabelo', 'HIG-001', '7891234567897', 'HairCare', 38.00, 18.00, 60, 15, 3, true, 29.90, 1, true, NOW(), NOW()),
  (9, 'Condicionador Reparador 500ml', 'Repara fios danificados', 'HIG-002', '7891234567898', 'HairCare', 42.00, 20.00, 55, 15, 3, false, NULL, 1, true, NOW(), NOW()),
  (10, 'Sabonete Líquido Premium', 'Fragrância suave e duradoura', 'HIG-003', '7891234567899', 'CleanSoft', 28.00, 12.00, 70, 20, 3, true, 22.90, 1, true, NOW(), NOW()),
  (11, 'Desodorante Antitranspirante', 'Proteção 48h', 'HIG-004', '7891234567800', 'FreshDay', 22.00, 10.00, 100, 25, 3, false, NULL, 1, true, NOW(), NOW()),
  
  -- Presentes & Kits (categoria 4)
  (12, 'Kit Perfume + Body Splash', 'Conjunto completo de fragrâncias', 'KIT-001', '7891234567801', 'Gift Box', 280.00, 150.00, 20, 5, 4, true, 249.90, 1, true, NOW(), NOW()),
  (13, 'Kit Maquiagem Completo', 'Base, batom, sombras e máscara', 'KIT-002', '7891234567802', 'Makeup Box', 350.00, 180.00, 15, 5, 4, false, NULL, 1, true, NOW(), NOW()),
  (14, 'Kit Presente Spa', 'Sabonetes e hidratantes especiais', 'KIT-003', '7891234567803', 'Relax Box', 180.00, 90.00, 25, 8, 4, false, NULL, 1, true, NOW(), NOW()),
  (15, 'Kit Cabelos Profissional', 'Shampoo, condicionador e máscara', 'KIT-004', '7891234567804', 'Hair Box', 220.00, 110.00, 3, 5, 4, false, NULL, 1, true, NOW(), NOW());

-- =====================================================
-- PRODUTOS - CAROL COSMÉTICOS (15 produtos, 7 em promoção)
-- =====================================================
INSERT INTO products (id, name, description, sku, barcode, brand, sale_price, cost_price, stock_quantity, min_stock, category_id, is_on_sale, promotional_price, company_id, is_active, created_at, updated_at)
VALUES
  -- Perfumes (categoria 5)
  (16, 'Perfume Floral Intenso', 'Aroma delicado e marcante', 'PERF-101', '7891234567805', 'Essence', 320.00, 180.00, 30, 8, 5, true, 279.90, 2, true, NOW(), NOW()),
  (17, 'Perfume Amadeirado', 'Fragrância sofisticada', 'PERF-102', '7891234567806', 'Essence', 280.00, 150.00, 35, 10, 5, false, NULL, 2, true, NOW(), NOW()),
  (18, 'Perfume Cítrico Fresh', 'Refrescância duradoura', 'PERF-103', '7891234567807', 'FreshScent', 200.00, 110.00, 45, 12, 5, true, 169.90, 2, true, NOW(), NOW()),
  
  -- Cosméticos (categoria 6)
  (19, 'Primer Facial', 'Prepara a pele para maquiagem', 'COS-101', '7891234567808', 'BeautyPro', 70.00, 35.00, 40, 10, 6, true, 59.90, 2, true, NOW(), NOW()),
  (20, 'Blush Compacto', 'Efeito natural e iluminado', 'COS-102', '7891234567809', 'BeautyPro', 55.00, 28.00, 60, 15, 6, false, NULL, 2, true, NOW(), NOW()),
  (21, 'Iluminador em Pó', 'Brilho sutil e elegante', 'COS-103', '7891234567810', 'GlowUp', 80.00, 40.00, 35, 10, 6, true, 69.90, 2, true, NOW(), NOW()),
  (22, 'Delineador à Prova d Água', 'Traço perfeito o dia todo', 'COS-104', '7891234567811', 'LinePerfect', 40.00, 20.00, 70, 18, 6, false, NULL, 2, true, NOW(), NOW()),
  
  -- Higiene Pessoal (categoria 7)
  (23, 'Creme Hidratante Corporal', 'Hidratação intensa 24h', 'HIG-101', '7891234567812', 'SkinCare', 45.00, 22.00, 50, 12, 7, true, 39.90, 2, true, NOW(), NOW()),
  (24, 'Esfoliante Facial', 'Remove impurezas e células mortas', 'HIG-102', '7891234567813', 'SkinCare', 58.00, 28.00, 40, 10, 7, false, NULL, 2, true, NOW(), NOW()),
  (25, 'Protetor Solar FPS 50', 'Proteção alta contra raios UV', 'HIG-103', '7891234567814', 'SunProtect', 75.00, 38.00, 65, 15, 7, true, 64.90, 2, true, NOW(), NOW()),
  (26, 'Loção Corporal Perfumada', 'Hidrata e perfuma', 'HIG-104', '7891234567815', 'BodyLux', 52.00, 26.00, 45, 12, 7, false, NULL, 2, true, NOW(), NOW()),
  
  -- Presentes & Kits (categoria 8)
  (27, 'Kit Skincare Completo', 'Limpeza, tonificação e hidratação', 'KIT-101', '7891234567816', 'Skin Box', 320.00, 160.00, 18, 5, 8, true, 279.90, 2, true, NOW(), NOW()),
  (28, 'Kit Perfume Duo', 'Dois perfumes complementares', 'KIT-102', '7891234567817', 'Scent Box', 450.00, 230.00, 12, 5, 8, false, NULL, 2, true, NOW(), NOW()),
  (29, 'Kit Corpo e Banho', 'Sabonete, esfoliante e hidratante', 'KIT-103', '7891234567818', 'Bath Box', 160.00, 80.00, 22, 8, 8, false, NULL, 2, true, NOW(), NOW()),
  (30, 'Kit Unhas Premium', 'Esmaltes e tratamentos', 'KIT-104', '7891234567819', 'Nail Box', 2, 5, 4, 5, 8, false, NULL, 2, true, NOW(), NOW());

-- =====================================================
-- CLIENTES (5 por empresa)
-- =====================================================
INSERT INTO customers (id, name, cpf, email, phone, address, city, state, zip_code, birth_date, company_id, is_active, created_at, updated_at)
VALUES
  -- Clientes Taty
  (1, 'Maria Silva', '12345678901', 'maria@email.com', '11987654321', 'Rua A, 100', 'São Paulo', 'SP', '01000-000', '1990-05-15', 1, true, NOW(), NOW()),
  (2, 'João Santos', '23456789012', 'joao@email.com', '11987654322', 'Rua B, 200', 'São Paulo', 'SP', '02000-000', '1985-08-20', 1, true, NOW(), NOW()),
  (3, 'Ana Costa', '34567890123', 'ana@email.com', '11987654323', 'Rua C, 300', 'São Paulo', 'SP', '03000-000', '1992-11-10', 1, true, NOW(), NOW()),
  (4, 'Pedro Oliveira', '45678901234', 'pedro@email.com', '11987654324', 'Rua D, 400', 'São Paulo', 'SP', '04000-000', '1988-03-25', 1, true, NOW(), NOW()),
  (5, 'Carla Souza', '56789012345', 'carla@email.com', '11987654325', 'Rua E, 500', 'São Paulo', 'SP', '05000-000', '1995-07-30', 1, true, NOW(), NOW()),
  
  -- Clientes Carol
  (6, 'Juliana Lima', '67890123456', 'juliana@email.com', '21987654321', 'Av. X, 100', 'Rio de Janeiro', 'RJ', '20000-000', '1991-04-12', 2, true, NOW(), NOW()),
  (7, 'Roberto Alves', '78901234567', 'roberto@email.com', '21987654322', 'Av. Y, 200', 'Rio de Janeiro', 'RJ', '21000-000', '1987-09-18', 2, true, NOW(), NOW()),
  (8, 'Fernanda Dias', '89012345678', 'fernanda@email.com', '21987654323', 'Av. Z, 300', 'Rio de Janeiro', 'RJ', '22000-000', '1993-12-05', 2, true, NOW(), NOW()),
  (9, 'Carlos Mendes', '90123456789', 'carlos@email.com', '21987654324', 'Rua W, 400', 'Rio de Janeiro', 'RJ', '23000-000', '1989-06-22', 2, true, NOW(), NOW()),
  (10, 'Patricia Rocha', '01234567890', 'patricia@email.com', '21987654325', 'Rua V, 500', 'Rio de Janeiro', 'RJ', '24000-000', '1994-01-14', 2, true, NOW(), NOW());

-- =====================================================
-- VENDAS E ITENS - TATY PERFUMARIA
-- =====================================================

-- Venda 1: À vista (Maria Silva)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (1, 1, 1, 1, 'cash', 'completed', 799.80, 50.00, 749.80, 1, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (1, 1, 2, 299.90, 599.80),
  (1, 10, 1, 22.90, 22.90),
  (1, 8, 6, 29.90, 179.40);

-- Venda 2: Crediário 3x (João Santos)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (2, 2, 1, 2, 'credit', 'completed', 569.80, 20.00, 549.80, 3, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (2, 3, 1, 449.90, 449.90),
  (2, 6, 1, 99.90, 99.90),
  (2, 8, 2, 29.90, 59.80);

INSERT INTO installments (sale_id, customer_id, company_id, installment_number, amount, due_date, status, created_at, updated_at)
VALUES
  (2, 2, 1, 1, 183.27, CURRENT_DATE + INTERVAL '30 days', 'pending', NOW(), NOW()),
  (2, 2, 1, 2, 183.27, CURRENT_DATE + INTERVAL '60 days', 'pending', NOW(), NOW()),
  (2, 2, 1, 3, 183.26, CURRENT_DATE + INTERVAL '90 days', 'pending', NOW(), NOW());

-- Venda 3: PIX (Ana Costa)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (3, 3, 1, 1, 'pix', 'completed', 319.70, 0.00, 319.70, 1, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (3, 4, 2, 69.90, 139.80),
  (3, 2, 1, 180.00, 180.00);

-- =====================================================
-- VENDAS E ITENS - CAROL COSMÉTICOS
-- =====================================================

-- Venda 4: À vista (Juliana Lima)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (4, 6, 2, 3, 'cash', 'completed', 449.70, 30.00, 419.70, 1, NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (4, 16, 1, 279.90, 279.90),
  (4, 19, 1, 59.90, 59.90),
  (4, 21, 1, 69.90, 69.90),
  (4, 23, 1, 39.90, 39.90);

-- Venda 5: Crediário 6x (Roberto Alves)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (5, 7, 2, 4, 'credit', 'completed', 649.70, 50.00, 599.70, 6, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (5, 27, 1, 279.90, 279.90),
  (5, 18, 1, 169.90, 169.90),
  (5, 25, 3, 64.90, 194.70),
  (5, 24, 1, 58.00, 58.00);

INSERT INTO installments (sale_id, customer_id, company_id, installment_number, amount, due_date, status, created_at, updated_at)
VALUES
  (5, 7, 2, 1, 99.95, CURRENT_DATE + INTERVAL '30 days', 'pending', NOW(), NOW()),
  (5, 7, 2, 2, 99.95, CURRENT_DATE + INTERVAL '60 days', 'pending', NOW(), NOW()),
  (5, 7, 2, 3, 99.95, CURRENT_DATE + INTERVAL '90 days', 'pending', NOW(), NOW()),
  (5, 7, 2, 4, 99.95, CURRENT_DATE + INTERVAL '120 days', 'pending', NOW(), NOW()),
  (5, 7, 2, 5, 99.95, CURRENT_DATE + INTERVAL '150 days', 'pending', NOW(), NOW()),
  (5, 7, 2, 6, 99.95, CURRENT_DATE + INTERVAL '180 days', 'pending', NOW(), NOW());

-- Venda 6: PIX (Fernanda Dias)
INSERT INTO sales (id, customer_id, company_id, user_id, payment_type, status, subtotal, discount_amount, total_amount, installments_count, created_at, updated_at)
VALUES (6, 8, 2, 3, 'pix', 'completed', 229.70, 10.00, 219.70, 1, NOW(), NOW());

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price)
VALUES
  (6, 21, 1, 69.90, 69.90),
  (6, 29, 1, 160.00, 160.00);

-- =====================================================
-- RELATÓRIO FINAL
-- =====================================================
SELECT 
    'EMPRESAS' as tabela, 
    COUNT(*)::text as quantidade 
FROM companies

UNION ALL

SELECT 
    'CATEGORIAS' as tabela, 
    COUNT(*)::text as quantidade 
FROM categories

UNION ALL

SELECT 
    'PRODUTOS' as tabela, 
    COUNT(*)::text as quantidade 
FROM products

UNION ALL

SELECT 
    'PRODUTOS EM PROMOÇÃO' as tabela, 
    COUNT(*)::text as quantidade 
FROM products 
WHERE is_on_sale = true

UNION ALL

SELECT 
    'CLIENTES' as tabela, 
    COUNT(*)::text as quantidade 
FROM customers

UNION ALL

SELECT 
    'USUÁRIOS' as tabela, 
    COUNT(*)::text as quantidade 
FROM users

UNION ALL

SELECT 
    'VENDAS' as tabela, 
    COUNT(*)::text as quantidade 
FROM sales

UNION ALL

SELECT 
    'ITENS DE VENDA' as tabela, 
    COUNT(*)::text as quantidade 
FROM sale_items

UNION ALL

SELECT 
    'PARCELAS' as tabela, 
    COUNT(*)::text as quantidade 
FROM installments

ORDER BY tabela;

-- Verificação de integridade das categorias em produtos
SELECT 
    'PRODUTOS COM CATEGORIA' as status,
    COUNT(*)::text as quantidade
FROM products
WHERE category_id IS NOT NULL

UNION ALL

SELECT 
    'PRODUTOS SEM CATEGORIA' as status,
    COUNT(*)::text as quantidade
FROM products
WHERE category_id IS NULL;
