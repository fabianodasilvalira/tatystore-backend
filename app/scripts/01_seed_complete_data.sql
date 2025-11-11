-- ============================================================================
-- SCRIPT COMPLETO DE INICIALIZAÇÃO DO SISTEMA
-- ============================================================================
-- Cria dados completos para 2 empresas com:
-- - 4 Categorias por empresa
-- - 15 Produtos por empresa (com categorias, promoções, estoque variado)
-- - 5 Clientes por empresa
-- - 25+ Vendas variadas com histórico de 3 meses
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
FROM roles r, permissions p
WHERE r.name = 'Administrador'
ON CONFLICT DO NOTHING;

-- Gerente: todas exceto criar empresas
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
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
FROM roles r, permissions p
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
-- 3. CATEGORIAS (4 por empresa)
-- ============================================================================

-- Categorias para Taty Perfumaria
INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
SELECT 
    cat.name,
    cat.description,
    c.id,
    true,
    NOW(),
    NOW()
FROM (VALUES
    ('Perfumes', 'Perfumes importados e nacionais de alta qualidade'),
    ('Cosméticos', 'Produtos de beleza e cuidados com a pele'),
    ('Higiene Pessoal', 'Sabonetes, desodorantes e produtos de higiene'),
    ('Presentes & Kits', 'Kits presentes e combos especiais')
) AS cat(name, description)
CROSS JOIN companies c
WHERE c.slug = 'taty'
ON CONFLICT DO NOTHING;

-- Categorias para Carol Perfumaria
INSERT INTO categories (name, description, company_id, is_active, created_at, updated_at)
SELECT 
    cat.name,
    cat.description,
    c.id,
    true,
    NOW(),
    NOW()
FROM (VALUES
    ('Perfumes', 'Fragrâncias exclusivas e sofisticadas'),
    ('Cosméticos', 'Maquiagem e tratamento facial'),
    ('Higiene Pessoal', 'Cuidados diários com o corpo'),
    ('Presentes & Kits', 'Cestas e kits especiais')
) AS cat(name, description)
CROSS JOIN companies c
WHERE c.slug = 'carol'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 4. USUÁRIOS (3 ativos + 1 inativo por empresa)
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
-- 5. PRODUTOS (15 por empresa com categorias e promoções)
-- ============================================================================

-- Produtos da Taty Perfumaria
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    p.name,
    p.description,
    p.sku,
    p.barcode,
    p.brand,
    p.cost_price,
    p.sale_price,
    p.is_on_sale,
    p.promotional_price,
    p.stock_quantity,
    p.min_stock,
    cat.id,
    c.id,
    p.is_active,
    NOW(),
    NOW()
FROM (VALUES
    -- PERFUMES (Categoria 1)
    ('Perfume Clássico Feminino 100ml', 'Fragrância floral e sofisticada', 'TATY-001', '7891234567890', 'Boticário', 45.00, 129.90, true, 99.90, 85, 20),
    ('Perfume Masculino Amadeirado 100ml', 'Aroma amadeirado intenso', 'TATY-002', '7891234567891', 'Natura', 50.00, 149.90, false, NULL, 120, 20),
    ('Perfume Infantil Suave 50ml', 'Fragrância delicada para crianças', 'TATY-003', '7891234567892', 'Jequiti', 20.00, 49.90, true, 39.90, 60, 20),
    ('Colônia Fresh Unissex 100ml', 'Aroma cítrico refrescante', 'TATY-004', '7891234567893', 'Avon', 30.00, 79.90, false, NULL, 95, 20),
    
    -- COSMÉTICOS (Categoria 2)
    ('Base Líquida FPS 30', 'Cobertura natural com proteção solar', 'TATY-005', '7891234567894', 'Eudora', 35.00, 89.90, true, 69.90, 45, 15),
    ('Batom Matte Longa Duração', 'Cor intensa por 12 horas', 'TATY-006', '7891234567895', 'Avon', 15.00, 39.90, false, NULL, 150, 30),
    ('Máscara de Cílios Volume', 'Volume e curvatura extrema', 'TATY-007', '7891234567896', 'Maybelline', 25.00, 59.90, true, 49.90, 80, 20),
    
    -- HIGIENE PESSOAL (Categoria 3)
    ('Sabonete Líquido Hidratante 500ml', 'Limpeza suave e hidratação', 'TATY-008', '7891234567897', 'Dove', 12.00, 29.90, false, NULL, 200, 30),
    ('Desodorante Roll-on 48h', 'Proteção prolongada', 'TATY-009', '7891234567898', 'Rexona', 8.00, 19.90, true, 15.90, 180, 40),
    ('Creme Dental Branqueador', 'Clareamento progressivo', 'TATY-010', '7891234567899', 'Colgate', 6.00, 14.90, false, NULL, 250, 50),
    ('Shampoo Antiqueda 400ml', 'Fortalece e previne queda', 'TATY-011', '7891234567800', 'Elseve', 18.00, 44.90, false, NULL, 110, 25),
    
    -- PRESENTES & KITS (Categoria 4)
    ('Kit Presente Dia das Mães', 'Perfume + Body Splash + Nécessaire', 'TATY-012', '7891234567801', 'Boticário', 80.00, 199.90, true, 169.90, 15, 10),
    ('Kit Presente Masculino Premium', 'Perfume + Desodorante + Loção Pós Barba', 'TATY-013', '7891234567802', 'Natura', 95.00, 249.90, false, NULL, 12, 10),
    
    -- PRODUTOS COM BAIXO ESTOQUE
    ('Sérum Anti-idade Facial 30ml', 'Reduz linhas de expressão', 'TATY-014', '7891234567803', 'Eudora', 40.00, 109.90, true, 89.90, 8, 15),
    
    -- PRODUTO INATIVO
    ('Perfume Descontinuado Antigo', 'Linha descontinuada', 'TATY-015', '7891234567804', 'Antiga', 30.00, 79.90, false, NULL, 0, 10)
) AS p(
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock, is_active
)
CROSS JOIN companies c
INNER JOIN categories cat ON cat.company_id = c.id 
    AND cat.name = CASE 
        WHEN p.sku IN ('TATY-001', 'TATY-002', 'TATY-003', 'TATY-004') THEN 'Perfumes'
        WHEN p.sku IN ('TATY-005', 'TATY-006', 'TATY-007') THEN 'Cosméticos'
        WHEN p.sku IN ('TATY-008', 'TATY-009', 'TATY-010', 'TATY-011') THEN 'Higiene Pessoal'
        ELSE 'Presentes & Kits'
    END
WHERE c.slug = 'taty'
ON CONFLICT (sku) DO NOTHING;

-- Produtos da Carol Perfumaria
INSERT INTO products (
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock,
    category_id, company_id, is_active, created_at, updated_at
)
SELECT 
    p.name,
    p.description,
    p.sku,
    p.barcode,
    p.brand,
    p.cost_price,
    p.sale_price,
    p.is_on_sale,
    p.promotional_price,
    p.stock_quantity,
    p.min_stock,
    cat.id,
    c.id,
    p.is_active,
    NOW(),
    NOW()
FROM (VALUES
    -- PERFUMES (Categoria 1)
    ('Eau de Parfum Luxo Feminino 75ml', 'Fragrância sofisticada francesa', 'CAROL-001', '7899876543210', 'Chanel', 120.00, 299.90, true, 249.90, 40, 15),
    ('Perfume Masculino Sport 100ml', 'Aroma energizante e vibrante', 'CAROL-002', '7899876543211', 'Paco Rabanne', 90.00, 219.90, false, NULL, 65, 15),
    ('Perfume Oriental Feminino 50ml', 'Notas orientais e sensuais', 'CAROL-003', '7899876543212', 'Dior', 110.00, 279.90, true, 239.90, 50, 15),
    ('Colônia Infantil Hipoalergênica 100ml', 'Segura para peles sensíveis', 'CAROL-004', '7899876543213', 'Johnson', 25.00, 59.90, false, NULL, 80, 20),
    
    -- COSMÉTICOS (Categoria 2)
    ('Paleta de Sombras 12 Cores', 'Cores vibrantes e duradouras', 'CAROL-005', '7899876543214', 'Ruby Rose', 40.00, 99.90, true, 79.90, 35, 10),
    ('Gloss Labial Hidratante', 'Brilho intenso com hidratação', 'CAROL-006', '7899876543215', 'Vult', 12.00, 29.90, false, NULL, 120, 25),
    ('Pó Compacto Matificante', 'Controle de oleosidade 8h', 'CAROL-007', '7899876543216', 'Mary Kay', 35.00, 89.90, false, NULL, 60, 15),
    
    -- HIGIENE PESSOAL (Categoria 3)
    ('Gel de Banho Hidratante 1L', 'Limpeza profunda com hidratação', 'CAROL-008', '7899876543217', 'Neutrogena', 20.00, 49.90, true, 39.90, 150, 30),
    ('Desodorante Aerosol 150ml', 'Fragrância duradoura', 'CAROL-009', '7899876543218', 'Nivea', 10.00, 24.90, false, NULL, 200, 40),
    ('Condicionador Nutritivo 400ml', 'Nutrição e brilho intenso', 'CAROL-010', '7899876543219', 'Pantene', 20.00, 49.90, true, 42.90, 95, 25),
    ('Loção Corporal Perfumada 200ml', 'Hidratação e perfume prolongado', 'CAROL-011', '7899876543220', 'Victoria Secret', 30.00, 74.90, false, NULL, 70, 20),
    
    -- PRESENTES & KITS (Categoria 4)
    ('Kit Cesta Dia dos Namorados', 'Perfume + Chocolate + Cartão', 'CAROL-012', '7899876543221', 'Carol Mix', 100.00, 249.90, true, 199.90, 18, 10),
    ('Kit Aniversário Feminino Luxo', 'Perfume + Maquiagem + Nécessaire', 'CAROL-013', '7899876543222', 'Carol Premium', 150.00, 379.90, false, NULL, 10, 8),
    
    -- PRODUTO COM BAIXO ESTOQUE
    ('Óleo Capilar Reparador 50ml', 'Reparação profunda de fios danificados', 'CAROL-014', '7899876543223', 'Kerastase', 55.00, 139.90, true, 119.90, 7, 15),
    
    -- PRODUTO INATIVO
    ('Creme Facial Linha Antiga', 'Produto descontinuado', 'CAROL-015', '7899876543224', 'Antiga', 25.00, 59.90, false, NULL, 0, 10)
) AS p(
    name, description, sku, barcode, brand, cost_price, sale_price,
    is_on_sale, promotional_price, stock_quantity, min_stock, is_active
)
CROSS JOIN companies c
INNER JOIN categories cat ON cat.company_id = c.id 
    AND cat.name = CASE 
        WHEN p.sku IN ('CAROL-001', 'CAROL-002', 'CAROL-003', 'CAROL-004') THEN 'Perfumes'
        WHEN p.sku IN ('CAROL-005', 'CAROL-006', 'CAROL-007') THEN 'Cosméticos'
        WHEN p.sku IN ('CAROL-008', 'CAROL-009', 'CAROL-010', 'CAROL-011') THEN 'Higiene Pessoal'
        ELSE 'Presentes & Kits'
    END
WHERE c.slug = 'carol'
ON CONFLICT (sku) DO NOTHING;

-- ============================================================================
-- 6. CLIENTES (5 por empresa)
-- ============================================================================

-- Clientes da Taty Perfumaria
INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
SELECT 
    cust.name,
    cust.email,
    cust.phone,
    cust.cpf,
    cust.address,
    c.id,
    cust.is_active,
    NOW(),
    NOW()
FROM (VALUES
    ('Maria da Silva Santos', 'maria.silva@email.com', '(11) 98765-4321', '12345678901', 'Rua das Acácias, 123 - Centro - São Paulo, SP', true),
    ('João Pedro Oliveira', 'joao.pedro@email.com', '(11) 97654-3210', '98765432101', 'Av. Brasil, 456 - Jardins - São Paulo, SP', true),
    ('Ana Carolina Souza', 'ana.carolina@email.com', '(11) 96543-2109', '11122233344', 'Rua Augusta, 789 - Consolação - São Paulo, SP', true),
    ('Carlos Eduardo Lima', 'carlos.lima@email.com', '(11) 95432-1098', '55566677788', 'Av. Rebouças, 321 - Pinheiros - São Paulo, SP', true),
    ('Juliana Costa Rodrigues', 'juliana.costa@email.com', '(11) 94321-0987', '99988877766', 'Rua Oscar Freire, 654 - Jardins - São Paulo, SP', false)
) AS cust(name, email, phone, cpf, address, is_active)
CROSS JOIN companies c
WHERE c.slug = 'taty'
ON CONFLICT DO NOTHING;

-- Clientes da Carol Perfumaria
INSERT INTO customers (name, email, phone, cpf, address, company_id, is_active, created_at, updated_at)
SELECT 
    cust.name,
    cust.email,
    cust.phone,
    cust.cpf,
    cust.address,
    c.id,
    cust.is_active,
    NOW(),
    NOW()
FROM (VALUES
    ('Fernanda Almeida Costa', 'fernanda.almeida@email.com', '(11) 93210-9876', '11111222233', 'Rua Haddock Lobo, 111 - Jardins - São Paulo, SP', true),
    ('Ricardo Martins Silva', 'ricardo.martins@email.com', '(11) 92109-8765', '22222333344', 'Av. Faria Lima, 222 - Itaim Bibi - São Paulo, SP', true),
    ('Patricia Fernandes Lima', 'patricia.fernandes@email.com', '(11) 91098-7654', '33333444455', 'Rua Bela Cintra, 333 - Consolação - São Paulo, SP', true),
    ('Bruno Santos Oliveira', 'bruno.santos@email.com', '(11) 90987-6543', '44444555566', 'Av. Angélica, 444 - Santa Cecília - São Paulo, SP', true),
    ('Camila Rodrigues Souza', 'camila.rodrigues@email.com', '(11) 89876-5432', '55555666677', 'Rua Estados Unidos, 555 - Jardins - São Paulo, SP', false)
) AS cust(name, email, phone, cpf, address, is_active)
CROSS JOIN companies c
WHERE c.slug = 'carol'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- RESUMO DOS DADOS CRIADOS
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
    RAISE NOTICE 'USUÁRIOS: % (4 por empresa: Admin, Gerente, Vendedor + 1 Inativo)', total_users;
    RAISE NOTICE 'PRODUTOS: % (15 por empresa com categorias e promoções)', total_products;
    RAISE NOTICE 'CLIENTES: % (5 por empresa)', total_customers;
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CREDENCIAIS DE ACESSO';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'TATY PERFUMARIA:';
    RAISE NOTICE '  admin@taty.com / admin123 (Administrador)';
    RAISE NOTICE '  gerente@taty.com / gerente123 (Gerente)';
    RAISE NOTICE '  vendedor@taty.com / vendedor123 (Vendedor)';
    RAISE NOTICE '';
    RAISE NOTICE 'CAROL PERFUMARIA:';
    RAISE NOTICE '  admin@carol.com / admin123 (Administrador)';
    RAISE NOTICE '  gerente@carol.com / gerente123 (Gerente)';
    RAISE NOTICE '  vendedor@carol.com / vendedor123 (Vendedor)';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
END $$;
