import React, { useMemo } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Company, User } from '../types';
import { useAuth } from '../App';
import { logger } from '../utils/logger';
import { getFullUrl } from '../utils/urlUtils';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
    themeColor: string;
    user: User | null;
    company: Company | null;
    serverUrl: string;
}

// getFullUrl agora importado de utils/urlUtils.ts

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, themeColor, user, company, serverUrl }) => {
    const { logout } = useAuth();

    const menuGroups = useMemo(() => {
        if (!user) return [];

        const allMenuGroups: {
            title: string;
            items: { id: string; name: string; icon: string; path: string; roles: string[] }[];
        }[] = [
                {
                    title: 'Principal',
                    items: [
                        { id: 'dashboard', name: 'Dashboard', icon: 'dashboard', path: '/dashboard', roles: ['gerente', 'vendedor'] },
                        { id: 'storefront', name: 'Minha Vitrine', icon: 'store', path: `/store/${user.company_slug}`, roles: ['gerente', 'vendedor'] },
                    ]
                },
                {
                    title: 'Gestão',
                    items: [
                        { id: 'sales', name: 'Vendas', icon: 'point_of_sale', path: '/sales', roles: ['gerente', 'vendedor'] },
                        { id: 'products', name: 'Estoque', icon: 'inventory_2', path: '/products', roles: ['gerente', 'vendedor'] },
                        { id: 'categories', name: 'Categorias', icon: 'category', path: '/categories', roles: ['gerente', 'vendedor'] },
                        { id: 'customers', name: 'Clientes', icon: 'group', path: '/customers', roles: ['gerente', 'vendedor'] },
                        { id: 'installments', name: 'Parcelas', icon: 'request_quote', path: '/installments', roles: ['gerente', 'vendedor'] },
                    ]
                },
                {
                    title: 'Administrativo',
                    items: [
                        { id: 'reports', name: 'Relatórios', icon: 'bar_chart', path: '/reports', roles: ['gerente'] },
                        { id: 'company', name: 'Minha Empresa', icon: 'business', path: '/company', roles: ['gerente'] },
                        { id: 'users', name: 'Usuários', icon: 'manage_accounts', path: '/users', roles: ['gerente'] },
                        { id: 'companies', name: 'Empresas', icon: 'domain', path: '/companies', roles: ['admin'] },
                        { id: 'settings', name: 'Configurações', icon: 'settings', path: '/settings', roles: ['gerente', 'admin'] },
                    ]
                },
            ];

        const userRole = user.role.toLowerCase();

        return allMenuGroups
            .map(group => ({
                ...group,
                items: group.items.filter(item => item.roles.includes(userRole) || userRole === 'super admin' || userRole === 'admin')
            }))
            .filter(group => group.items.length > 0);

    }, [user]);

    const isWhiteTheme = themeColor === 'white';
    const headerBgColor = isWhiteTheme ? 'bg-white' : 'bg-primary-600';
    const headerTextColor = isWhiteTheme ? 'text-gray-900' : 'text-white';

    const linkClasses = ({ isActive }: { isActive?: boolean }) =>
        `flex items-center py-3 px-4 rounded-lg transition-all duration-200 ${isActive
            ? 'bg-primary-600 text-white shadow-md'
            : 'text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-700/20 hover:text-primary-600 dark:hover:text-primary-300'
        }`;

    const handleShareStorefront = async () => {
        if (!user?.company_slug) {
            alert("Não foi possível encontrar o link da sua vitrine.");
            return;
        }

        const storeUrl = `${window.location.origin}/#/store/${user.company_slug}`;
        const shareData = {
            title: `Vitrine de ${company?.name || 'Taty Store'}`,
            text: `Confira nossos produtos na vitrine online da ${company?.name || 'Taty Store'}!`,
            url: storeUrl,
        };

        if (navigator.share) {
            try {
                await navigator.share(shareData);
            } catch (err) {
                logger.error("Erro ao compartilhar", err, 'handleShareStorefront');
            }
        } else {
            try {
                await navigator.clipboard.writeText(storeUrl);
                alert('Link da vitrine copiado para a área de transferência!');
            } catch (err) {
                alert('Seu navegador não suporta compartilhamento. Copie o link manualmente: ' + storeUrl);
            }
        }
    };

    const handleLogout = () => {
        onClose();
        logout();
    };

    const logoSrc = getFullUrl(company?.logo_url, serverUrl);

    return (
        <>
            {/* Overlay for mobile */}
            <div
                className={`fixed inset-0 bg-black bg-opacity-50 z-30 transition-opacity lg:hidden ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                onClick={onClose}
            ></div>

            {/* Sidebar */}
            <aside className={`w-64 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 flex flex-col shadow-lg fixed lg:relative inset-y-0 left-0 z-40 transform transition-transform duration-300 ease-in-out lg:transform-none ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                <div className={`h-20 flex items-center justify-center px-4 ${headerBgColor}`}>
                    {company ? (
                        logoSrc ? (
                            <img src={logoSrc} alt={`${company.name} logo`} className="h-16 w-auto max-w-full rounded-lg object-contain" />
                        ) : (
                            <>
                                <span className={`material-symbols-outlined text-4xl ${headerTextColor}`}>storefront</span>
                                <h1 className={`text-xl font-bold ml-3 truncate ${headerTextColor}`}>{company.name}</h1>
                            </>
                        )
                    ) : (
                        <div className="flex items-center justify-center">
                            <div className="h-12 w-12 bg-gray-400/30 dark:bg-gray-600/30 rounded-lg animate-pulse"></div>
                            <div className="h-6 w-24 bg-gray-400/30 dark:bg-gray-600/30 rounded ml-3 animate-pulse"></div>
                        </div>
                    )}
                </div>
                <div className="flex-1 flex flex-col justify-between overflow-y-auto">
                    <nav className="px-4 py-2">
                        <ul>
                            {menuGroups.map((group) => (
                                <React.Fragment key={group.title}>
                                    <li className="px-4 pt-4 pb-2 text-xs font-bold uppercase text-gray-400 dark:text-gray-500 tracking-wider">
                                        {group.title}
                                    </li>
                                    {group.items.map(item => (
                                        <li key={item.id} className="mb-1">
                                            <NavLink
                                                to={item.path}
                                                onClick={onClose}
                                                className={linkClasses}
                                            >
                                                <span className="material-symbols-outlined mr-4">{item.icon}</span>
                                                <span className="font-medium">{item.name}</span>
                                            </NavLink>
                                        </li>
                                    ))}
                                </React.Fragment>
                            ))}
                        </ul>
                    </nav>

                    <div>
                        {/* Botões de Ação Rápida (Esconder do Super Admin) */}
                        {user.role.toLowerCase() !== 'super admin' && (
                            <div className="px-4 py-4 space-y-4">
                                <Link
                                    to="/sales/new"
                                    onClick={onClose}
                                    className="flex items-center justify-center w-full bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:bg-primary-700 transition-transform hover:scale-105"
                                >
                                    <span className="material-symbols-outlined mr-2">add_shopping_cart</span>
                                    Nova Venda
                                </Link>
                                <button
                                    onClick={handleShareStorefront}
                                    disabled={!user?.company_slug}
                                    className="flex items-center justify-center w-full bg-gray-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:bg-gray-700 transition-transform hover:scale-105 disabled:bg-gray-400"
                                >
                                    <span className="material-symbols-outlined mr-2">share</span>
                                    Encaminhar Vitrine
                                </button>
                            </div>
                        )}
                        <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700">
                            <NavLink
                                to="/profile"
                                onClick={onClose}
                                className={linkClasses}
                            >
                                <span className="material-symbols-outlined mr-4">person</span>
                                <span className="font-medium">Meu Perfil</span>
                            </NavLink>
                            <button
                                onClick={handleLogout}
                                className="flex items-center w-full py-3 px-4 rounded-lg transition-all duration-200 text-gray-600 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-700/20 hover:text-red-600 dark:hover:text-red-300 mt-1"
                            >
                                <span className="material-symbols-outlined mr-4">logout</span>
                                <span className="font-medium">Sair</span>
                            </button>
                        </div>
                        <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700 text-center text-xs text-gray-500 dark:text-gray-400">
                            <p>
                                Suporte via <a href="mailto:suporte@donnaparfum.com" className="font-semibold text-primary-600 dark:text-primary-400 hover:underline">email</a>
                            </p>
                            <p className="mt-1">
                                Desenvolvido por <a href="https://www.linkedin.com/in/fabiano-lira-5a02251a3/" target="_blank" rel="noopener noreferrer" className="font-semibold text-primary-600 dark:text-primary-400 hover:underline">Fabiano Lira</a>
                            </p>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;