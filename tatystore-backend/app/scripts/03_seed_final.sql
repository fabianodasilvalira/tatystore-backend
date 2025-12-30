-- ============================================================================
-- SCRIPT COMPLETO DE INICIALIZAÇÃO DO SISTEMA - VERSÃO FINAL
-- ============================================================================
-- Este script cria dados completos para 2 empresas com:
-- - 4 Categorias por empresa (CORRIGIDO)
-- - 15 Produtos por empresa (com categorias, promoções, estoque variado)
-- - 5 Clientes por empresa
-- - Permissões e perfis completos
-- ============================================================================

-- ============================================================================
-- 1. PERMISSÕES E PERFIS
-- ============================================================================

-- Criar permissões
INSERT INTO permissions (code, description) VALUES
('products.view', 'Pode visualizar produtos'),
('products.create', 'Pode cadastrar novos produtos'),
('products.update', 'Pode editar informações gerais de produtos'),
('products.update_stock', 'Pode alterar o estoque de produtos'),
('customers.view', 'Pode visualizar clientes'),
('customers.create', 'Pode cadastrar novos clientes'),
('customers.update', 'Pode editar dados de clientes'),
('sales.create', 'Pode registrar vendas'),
('sales.cancel', 'Pode cancelar vendas'),
('reports.view', 'Pode visualizar relatórios'),
('companies.create', 'Pode criar novas empresas'),
('categories.view', 'Pode visualizar categorias'),
('categories.create', 'Pode criar categorias'),
('categories.update', 'Pode editar categorias'),
('categories.delete', 'Pode excluir categorias')
ON CONFLICT (code) DO NOTHING;

-- Criar perfis (roles)
INSERT INTO roles (name, is_active) VALUES
('Administrador', true),
('Gerente', true),
('Vendedor', true)
ON CONFLICT (name) DO NOTHING;

-- Associar permissões aos perfis
-- Administrador: todas as permissões
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'Administrador'
ON CONFLICT DO NOTHING;

-- Gerente: todas exceto criar empresas
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'Gerente'
  AND p.code IN (
    'products.view', 'products.create', 'products.update', 'products.update_stock',
    'customers.view', 'customers.create', 'customers.update',
    'sales.create', 'sales.cancel', 'reports.view',
    'categories.view', 'categories.create', 'categories.update', 'categories.delete'
  )
ON CONFLICT DO NOTHING;

-- Vendedor: apenas operações básicas
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'Vendedor'
  AND p.code IN (
    'products.view', 'customers.view', 'customers.create',
    'sales.create', 'categories.view'
  )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 2. EMPRESAS
-- ============================================================================

INSERT INTO companies (name, slug, cnpj, email, phone, address, is_active, created_at, updated_at) VALUES
('Taty Perfumaria', 'taty', '12345678000190', 'contato@taty.com', '(11) 99999-9999', 'Rua das Flores, 123 - Centro - São Paulo, SP', true, NOW(), NOW()),
('Carol Perfumaria', 'carol', '98765432000150', 'contato@carol.com', '(11) 88888-8888', 'Av. Paulista, 456 - Bela Vista - São Paulo, SP', true, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- 3. USUÁRIOS (4 por empresa: Admin, Gerente, Vendedor + 1 Inativo)
-- ============================================================================

-- Usuários da Taty Perfumaria
INSERT INTO users (name, email, password_hash, company_id, role_id, is_active, created_at, updated_at)
SELECT 
    u.name,
    u.email,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lNakjK6HnNt2', -- senha: admin123
    c.id,
    r.id,
    u.is_active,
    NOW(),
    NOW()
FROM (VALUES
    ('Admin Taty', 'admin@taty.com', 'Administrador', true),
    ('Gerente Taty', 'gerente@taty.com', 'Gerente', true),
    ('Vendedor Taty', 'vendedor@taty.com', 'Vendedor', true),
    ('Vendedor Inativo Taty', 'vendedor.inativo@taty.com', 'Vendedor', false)
) AS u(name, email, role_name, is_active)
CROSS JOIN companies c
INNER JOIN roles r ON r.name = u.role_name
WHERE c.slug = 'taty'
ON CONFLICT (email) DO NOTHING;

-- Usuários da Carol Perfumaria
INSERT INTO users (name, email, password_hash, company_id, role_id, is_active, created_at, updated_at)
SELECT 
    u.name,
    u.email,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lNakjK6HnNt2', -- senha: admin123
    c.id,
    r.id,
    u.is_active,
    NOW(),
    NOW()
FROM (VALUES
    ('Admin Carol', 'admin@carol.com', 'Administrador', true),
    ('Gerente Carol', 'gerente@carol.com', 'Gerente', true),
    ('Vendedor Carol', 'vendedor@carol.com', 'Vendedor', true),
    ('Vendedor Inativo Carol', 'vendedor.inativo@carol.com', 'Vendedor', false)
) AS u(name, email, role_name, is_active)
CROSS JOIN companies c
INNER JOIN roles r ON r.name = u.role_name
WHERE c.slug = 'carol'
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- 4. CATEGORIAS (4 por empresa) - CORRIGIDO SEM CONSTRAINT PROBLEMS
-- ============================================================================

DO $$
DECLARE
    v_company_id_taty INTEGER;
    v_company_id_carol INTEGER;
BEGIN
    -- Obter IDs das empresas
    SELECT id INTO v_company_id_taty FROM companies WHERE slug = 'taty';
    SELECT id INTO v_company_id_carol FROM companies WHERE slug = 'carol';
    
    -- Categorias para Taty Perfumaria
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Perfumes' AND company_id = v_company_id_taty) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Perfumes', 'Perfumes importados e nacionais de alta qualidade', v_company_id_taty, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Cosméticos' AND company_id = v_company_id_taty) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Cosméticos', 'Produtos de beleza e cuidados com a pele', v_company_id_taty, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Higiene Pessoal' AND company_id = v_company_id_taty) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Higiene Pessoal', 'Sabonetes, desodorantes e produtos de higiene', v_company_id_taty, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Presentes & Kits' AND company_id = v_company_id_taty) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Presentes & Kits', 'Kits presentes e combos especiais', v_company_id_taty, true, NOW(), NOW());
    END IF;
    
    -- Categorias para Carol Perfumaria
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Perfumes' AND company_id = v_company_id_carol) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Perfumes', 'Fragrâncias exclusivas e sofisticadas', v_company_id_carol, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Cosméticos' AND company_id = v_company_id_carol) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Cosméticos', 'Maquiagem e tratamento facial', v_company_id_carol, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Higiene Pessoal' AND company_id = v_company_id_carol) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Higiene Pessoal', 'Cuidados diários com o corpo', v_company_id_carol, true, NOW(), NOW());
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Presentes & Kits' AND company_id = v_company_id_carol) THEN
        INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
        VALUES ('Presentes & Kits', 'Cestas e kits especiais', v_company_id_carol, true, NOW(), NOW());
    END IF;
    
    RAISE NOTICE 'Categorias criadas com sucesso!';
END $$;

-- ============================================================================
-- 5. PRODUTOS (15 por empresa com todas as categorias)
-- ============================================================================

-- Produtos da Taty Perfumaria - PERFUMES
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Perfume Clássico Feminino 100ml',
    'Fragrância floral e sofisticada',
    'TATY-001',
    '7891234567890',
    'Boticário',
    45.00,
    129.90,
    true,
    99.90,
    85,
    20,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Perfume Masculino Amadeirado 100ml',
    'Aroma amadeirado intenso',
    'TATY-002',
    '7891234567891',
    'Natura',
    50.00,
    149.90,
    false,
    NULL,
    120,
    20,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Perfume Infantil Suave 50ml',
    'Fragrância delicada para crianças',
    'TATY-003',
    '7891234567892',
    'Jequiti',
    20.00,
    49.90,
    true,
    39.90,
    60,
    20,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Colônia Fresh Unissex 100ml',
    'Aroma cítrico refrescante',
    'TATY-004',
    '7891234567893',
    'Avon',
    30.00,
    79.90,
    false,
    NULL,
    95,
    20,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produtos da Taty Perfumaria - COSMÉTICOS
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Base Líquida FPS 30',
    'Cobertura natural com proteção solar',
    'TATY-005',
    '7891234567894',
    'Eudora',
    35.00,
    89.90,
    true,
    69.90,
    45,
    15,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Batom Matte Longa Duração',
    'Cor intensa por 12 horas',
    'TATY-006',
    '7891234567895',
    'Avon',
    15.00,
    39.90,
    false,
    NULL,
    150,
    30,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Máscara de Cílios Volume',
    'Volume e curvatura extrema',
    'TATY-007',
    '7891234567896',
    'Maybelline',
    25.00,
    59.90,
    true,
    49.90,
    80,
    20,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produtos da Taty Perfumaria - HIGIENE PESSOAL
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Sabonete Líquido Hidratante 500ml',
    'Limpeza suave e hidratação',
    'TATY-008',
    '7891234567897',
    'Dove',
    12.00,
    29.90,
    false,
    NULL,
    200,
    30,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Desodorante Roll-on 48h',
    'Proteção prolongada',
    'TATY-009',
    '7891234567898',
    'Rexona',
    8.00,
    19.90,
    true,
    15.90,
    180,
    40,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Creme Dental Branqueador',
    'Clareamento progressivo',
    'TATY-010',
    '7891234567899',
    'Colgate',
    6.00,
    14.90,
    false,
    NULL,
    250,
    50,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Shampoo Antiqueda 400ml',
    'Fortalece e previne queda',
    'TATY-011',
    '7891234567800',
    'Elseve',
    18.00,
    44.90,
    false,
    NULL,
    110,
    25,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produtos da Taty Perfumaria - PRESENTES & KITS
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Kit Presente Dia das Mães',
    'Perfume + Body Splash + Nécessaire',
    'TATY-012',
    '7891234567801',
    'Boticário',
    80.00,
    199.90,
    true,
    169.90,
    15,
    10,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Presentes & Kits'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Kit Presente Masculino Premium',
    'Perfume + Desodorante + Loção Pós Barba',
    'TATY-013',
    '7891234567802',
    'Natura',
    95.00,
    249.90,
    false,
    NULL,
    12,
    10,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Presentes & Kits'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produto com baixo estoque
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Sérum Anti-idade Facial 30ml',
    'Reduz linhas de expressão',
    'TATY-014',
    '7891234567803',
    'Eudora',
    40.00,
    109.90,
    true,
    89.90,
    8,
    15,
    cat.id,
    c.id,
    true,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produto inativo
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    'Perfume Descontinuado Antigo',
    'Linha descontinuada',
    'TATY-015',
    '7891234567804',
    'Antiga',
    30.00,
    79.90,
    false,
    NULL,
    0,
    10,
    cat.id,
    c.id,
    false,
    NOW(),
    NOW()
FROM companies c
INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes'
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- ============================================================================
-- PRODUTOS CAROL PERFUMARIA
-- ============================================================================

-- Perfumes
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Eau de Parfum Luxo Feminino 75ml', 'Fragrância sofisticada francesa', 'CAROL-001', '7899876543210', 'Chanel', 120.00, 299.90, true, 249.90, 40, 15, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Perfume Masculino Sport 100ml', 'Aroma energizante e vibrante', 'CAROL-002', '7899876543211', 'Paco Rabanne', 90.00, 219.90, false, NULL, 65, 15, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Perfume Oriental Feminino 50ml', 'Notas orientais e sensuais', 'CAROL-003', '7899876543212', 'Dior', 110.00, 279.90, true, 239.90, 50, 15, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Colônia Infantil Hipoalergênica 100ml', 'Segura para peles sensíveis', 'CAROL-004', '7899876543213', 'Johnson', 25.00, 59.90, false, NULL, 80, 20, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Perfumes' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- Cosméticos
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Paleta de Sombras 12 Cores', 'Cores vibrantes e duradouras', 'CAROL-005', '7899876543214', 'Ruby Rose', 40.00, 99.90, true, 79.90, 35, 10, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Gloss Labial Hidratante', 'Brilho intenso com hidratação', 'CAROL-006', '7899876543215', 'Vult', 12.00, 29.90, false, NULL, 120, 25, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Pó Compacto Matificante', 'Controle de oleosidade 8h', 'CAROL-007', '7899876543216', 'Mary Kay', 35.00, 89.90, false, NULL, 60, 15, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- Higiene Pessoal
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Gel de Banho Hidratante 1L', 'Limpeza profunda com hidratação', 'CAROL-008', '7899876543217', 'Neutrogena', 20.00, 49.90, true, 39.90, 150, 30, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Desodorante Aerosol 150ml', 'Fragrância duradoura', 'CAROL-009', '7899876543218', 'Nivea', 10.00, 24.90, false, NULL, 200, 40, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Condicionador Nutritivo 400ml', 'Nutrição e brilho intenso', 'CAROL-010', '7899876543219', 'Pantene', 20.00, 49.90, true, 42.90, 95, 25, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Loção Corporal Perfumada 200ml', 'Hidratação e perfume prolongado', 'CAROL-011', '7899876543220', 'Victoria Secret', 30.00, 74.90, false, NULL, 70, 20, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- Presentes & Kits
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Kit Cesta Dia dos Namorados', 'Perfume + Chocolate + Cartão', 'CAROL-012', '7899876543221', 'Carol Mix', 100.00, 249.90, true, 199.90, 18, 10, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Presentes & Kits' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Kit Aniversário Feminino Luxo', 'Perfume + Maquiagem + Nécessaire', 'CAROL-013', '7899876543222', 'Carol Premium', 150.00, 379.90, false, NULL, 10, 8, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Presentes & Kits' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- Baixo estoque
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Óleo Capilar Reparador 50ml', 'Reparação profunda de fios danificados', 'CAROL-014', '7899876543223', 'Kerastase', 55.00, 139.90, true, 119.90, 7, 15, cat.id, c.id, true, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Higiene Pessoal' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- Inativo
INSERT INTO products (name, description, sku, barcode, brand, cost_price, sale_price, is_on_sale, promotional_price, stock_quantity, min_stock, category_id, company_id, is_active, created_at, updated_at)
SELECT 'Creme Facial Linha Antiga', 'Produto descontinuado', 'CAROL-015', '7899876543224', 'Antiga', 25.00, 59.90, false, NULL, 0, 10, cat.id, c.id, false, NOW(), NOW()
FROM companies c INNER JOIN categories cat ON cat.company_id = c.id AND cat.name = 'Cosméticos' WHERE c.slug = 'carol' ON CONFLICT (sku) DO NOTHING;

-- ============================================================================
-- 6. CLIENTES (5 por empresa)
-- ============================================================================

-- Clientes da Taty Perfumaria
INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
SELECT cust.name, cust.email, cust.phone, cust.cpf, cust.address, c.id, cust.is_active, NOW(), NOW()
FROM (VALUES
    ('Maria da Silva Santos', 'maria.silva@email.com', '(11) 98765-4321', '12345678901', 'Rua das Acácias, 123 - Centro - São Paulo, SP', true),
    ('João Pedro Oliveira', 'joao.pedro@email.com', '(11) 97654-3210', '98765432101', 'Av. Brasil, 456 - Jardins - São Paulo, SP', true),
    ('Ana Carolina Souza', 'ana.carolina@email.com', '(11) 96543-2109', '11122233344', 'Rua Augusta, 789 - Consolação - São Paulo, SP', true),
    ('Carlos Eduardo Lima', 'carlos.lima@email.com', '(11) 95432-1098', '55566677788', 'Av. Rebouças, 321 - Pinheiros - São Paulo, SP', true),
    ('Juliana Costa Rodrigues', 'juliana.costa@email.com', '(11) 94321-0987', '99988877766', 'Rua Oscar Freire, 654 - Jardins - São Paulo, SP', false)
) AS cust(name, email, phone, cpf, address, is_active)
CROSS JOIN companies c WHERE c.slug = 'taty' ON CONFLICT DO NOTHING;

-- Clientes da Carol Perfumaria
INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
SELECT cust.name, cust.email, cust.phone, cust.cpf, cust.address, c.id, cust.is_active, NOW(), NOW()
FROM (VALUES
    ('Fernanda Almeida Costa', 'fernanda.almeida@email.com', '(11) 93210-9876', '11111222233', 'Rua Haddock Lobo, 111 - Jardins - São Paulo, SP', true),
    ('Ricardo Martins Silva', 'ricardo.martins@email.com', '(11) 92109-8765', '22222333344', 'Av. Faria Lima, 222 - Itaim Bibi - São Paulo, SP', true),
    ('Patricia Fernandes Lima', 'patricia.fernandes@email.com', '(11) 91098-7654', '33333444455', 'Rua Bela Cintra, 333 - Consolação - São Paulo, SP', true),
    ('Bruno Santos Oliveira', 'bruno.santos@email.com', '(11) 90987-6543', '44444555566', 'Av. Angélica, 444 - Santa Cecília - São Paulo, SP', true),
    ('Camila Rodrigues Souza', 'camila.rodrigues@email.com', '(11) 89876-5432', '55555666677', 'Rua Estados Unidos, 555 - Jardins - São Paulo, SP', false)
) AS cust(name, email, phone, cpf, address, is_active)
CROSS JOIN companies c WHERE c.slug = 'carol' ON CONFLICT DO NOTHING;

-- ============================================================================
-- RESUMO
-- ============================================================================

DO $$
DECLARE
    total_companies INTEGER;
    total_categories INTEGER;
    total_users INTEGER;
    total_products INTEGER;
    total_customers INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_companies FROM companies;
    SELECT COUNT(*) INTO total_categories FROM categories;
    SELECT COUNT(*) INTO total_users FROM users;
    SELECT COUNT(*) INTO total_products FROM products;
    SELECT COUNT(*) INTO total_customers FROM customers;
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'DADOS INICIALIZADOS COM SUCESSO!';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'EMPRESAS: %', total_companies;
    RAISE NOTICE 'CATEGORIAS: % (4 por empresa)', total_categories;
    RAISE NOTICE 'USUÁRIOS: % (4 por empresa)', total_users;
    RAISE NOTICE 'PRODUTOS: % (15 por empresa)', total_products;
    RAISE NOTICE 'CLIENTES: % (5 por empresa)', total_customers;
    RAISE NOTICE '';
    RAISE NOTICE 'CREDENCIAIS:';
    RAISE NOTICE '  admin@taty.com / admin123';
    RAISE NOTICE '  admin@carol.com / admin123';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
END $$;
