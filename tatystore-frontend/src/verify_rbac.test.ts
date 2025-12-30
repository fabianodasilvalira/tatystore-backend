import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// 1. Lógica do Sidebar.tsx (Replicada para Teste)
// ---------------------------------------------------------------------------
const getFilteredMenu = (userRole: string) => {
    // Menu Structure from Sidebar.tsx
    const allMenuGroups = [
        {
            title: 'Principal',
            items: [
                { id: 'dashboard', name: 'Dashboard', roles: ['gerente', 'vendedor'] },
                { id: 'storefront', name: 'Minha Vitrine', roles: ['gerente', 'vendedor'] },
            ]
        },
        {
            title: 'Gestão',
            items: [
                { id: 'sales', name: 'Vendas', roles: ['gerente', 'vendedor'] },
                { id: 'products', name: 'Estoque', roles: ['gerente', 'vendedor'] },
                { id: 'categories', name: 'Categorias', roles: ['gerente', 'vendedor'] },
                { id: 'customers', name: 'Clientes', roles: ['gerente', 'vendedor'] },
                { id: 'installments', name: 'Parcelas', roles: ['gerente', 'vendedor'] },
            ]
        },
        {
            title: 'Administrativo',
            items: [
                { id: 'reports', name: 'Relatórios', roles: ['gerente'] },
                { id: 'company', name: 'Minha Empresa', roles: ['gerente'] },
                { id: 'users', name: 'Usuários', roles: ['gerente'] },
                { id: 'companies', name: 'Empresas', roles: ['admin'] },
                { id: 'settings', name: 'Configurações', roles: ['gerente', 'admin'] },
            ]
        },
    ];

    const normalizedRole = userRole.toLowerCase();

    // LÓGICA EXATA usada no componente:
    return allMenuGroups
        .map(group => ({
            ...group,
            items: group.items.filter(item => item.roles.includes(normalizedRole) || normalizedRole === 'super admin' || normalizedRole === 'admin')
        }))
        .filter(group => group.items.length > 0);
};

// ---------------------------------------------------------------------------
// 2. Lógica do App.tsx ProtectedRoute (Replicada para Teste)
// ---------------------------------------------------------------------------
const checkRoutePermission = (userRole: string, allowedRoles: string[]) => {
    const normalized = userRole.toLowerCase();
    // LÓGICA EXATA usada no componente:
    return allowedRoles.includes(normalized) || normalized === 'admin' || normalized === 'super admin';
}

// ---------------------------------------------------------------------------
// SUÍTE DE TESTES
// ---------------------------------------------------------------------------
describe('Verificação de Segurança (RBAC) - Taty Store', () => {

    describe('Sidebar (Visibilidade do Menu)', () => {
        it('VENDEDOR: Não deve ver menu Administrativo', () => {
            const menu = getFilteredMenu('vendedor');
            const adminGroup = menu.find(g => g.title === 'Administrativo');
            expect(adminGroup).toBeUndefined(); // Grupo inteiro deve sumir
        });

        it('VENDEDOR: Deve ver apenas menus operacionais', () => {
            const menu = getFilteredMenu('vendedor');
            const titulos = menu.map(g => g.title);
            expect(titulos).toEqual(['Principal', 'Gestão']);

            // Check specific items
            const gestao = menu.find(g => g.title === 'Gestão')?.items.map(i => i.id);
            expect(gestao).toContain('sales');
            expect(gestao).toContain('products');
        });

        it('GERENTE: Deve ver menu Administrativo (exceto Super Admin)', () => {
            const menu = getFilteredMenu('gerente');
            const adminGroup = menu.find(g => g.title === 'Administrativo');
            expect(adminGroup).toBeDefined();

            const items = adminGroup?.items.map(i => i.id);
            expect(items).toContain('users');
            expect(items).toContain('settings');
            expect(items).not.toContain('companies'); // Companies é exclusivo de Admin
        });
    });

    describe('ProtectedRoute (Acesso a URLs)', () => {
        it('VENDEDOR: Acesso negado a rotas de Gerente', () => {
            const permission = checkRoutePermission('vendedor', ['gerente']);
            expect(permission).toBe(false);
        });

        it('VENDEDOR: Acesso negado a rotas de Admin', () => {
            const permission = checkRoutePermission('vendedor', ['admin']);
            expect(permission).toBe(false);
        });

        it('GERENTE: Acesso permitido a rotas de Gerente', () => {
            const permission = checkRoutePermission('gerente', ['gerente']);
            expect(permission).toBe(true);
        });

        it('ADMIN: Acesso irrestrito (God Mode)', () => {
            const permission = checkRoutePermission('admin', ['gerente', 'vendedor']);
            expect(permission).toBe(true);
        });
    });

    describe('Falsos Positivos (Regression Test)', () => {
        it('Role parcial "gerente-logistica" não deve acessar área de "gerente"', () => {
            // Testando se o bug do .includes() foi resolvido
            const menu = getFilteredMenu('gerente-logistica');
            const adminGroup = menu.find(g => g.title === 'Administrativo');

            // Com .includes() antigo, isso falharia (daria acesso). Com a correção, deve bloquear.
            expect(adminGroup).toBeUndefined();
        });
    });
});
