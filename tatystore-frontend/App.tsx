
import React, { useState, useCallback, useMemo, useEffect, createContext, useContext } from 'react';
import { Routes, Route, Outlet, useLocation, Navigate, useNavigate } from 'react-router-dom';
import { Product, Customer, Sale, User, AuthContextType, Installment, InstallmentStatus, SaleItem, Category, Company, PaymentMethod } from './types';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import ProductImport from './pages/ProductImport';
import Sales from './pages/Sales';
import Customers from './pages/Customers';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import LoginPage from './pages/Login';
import CompaniesPage from './pages/Companies';
import ToastContainer from './components/ToastContainer';
import UsersPage from './pages/Users';
import CategoriesPage from './pages/Categories';
import StorefrontPage from './pages/store/StorefrontPage';
import ProductDetailPage from './pages/store/ProductDetailPage';
import LandingPage from './pages/LandingPage';
import InstallmentsPage from './pages/Installments';
import CompanyPage from './pages/CompanyPage';
import Profile from './pages/Profile';
import { API_BASE_URL, SERVER_BASE_URL } from './config/api';
import { logger } from './utils/logger';
import { handleApiError } from './utils/errorHandler';
import { safeParseDate } from './utils/dateUtils';

// safeParseDate agora importado de utils/dateUtils.ts


// --- Contexto de Autenticação ---
const AuthContext = createContext<AuthContextType | null>(null);
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

// --- Hooks Persistentes ---
function usePersistentState<T>(key: string, initialState: T): [T, React.Dispatch<React.SetStateAction<T>>] {
    const [state, setState] = useState<T>(() => {
        try {
            const storageValue = window.localStorage.getItem(key);
            if (storageValue) {
                return JSON.parse(storageValue, (k, v) => {
                    if (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/.test(v)) {
                        return new Date(v);
                    }
                    return v;
                });
            }
        } catch (error) {
            logger.error(`Error reading localStorage key "${key}"`, error, 'usePersistentState');
        }
        return initialState;
    });

    useEffect(() => {
        try {
            window.localStorage.setItem(key, JSON.stringify(state));
        } catch (error) {
            logger.error(`Error setting localStorage key "${key}"`, error, 'usePersistentState');
        }
    }, [key, state]);

    return [state, setState];
}

// --- Hook de Debounce ---
export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}


const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = usePersistentState<User | null>('user', null);
    const [tokens, setTokens] = usePersistentState<{ access_token: string, redirect_url: string } | null>('tokens', null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        // Simula a verificação inicial do token
        setIsLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        // Conectando ao backend 
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                let errorMessage = 'Credenciais inválidas ou erro no servidor.';
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.message) {
                        errorMessage = Array.isArray(errorData.message) ? errorData.message.join(', ') : errorData.message;
                    }
                } catch (e) {
                    // Falha ao analisar o JSON, use a mensagem padrão
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();

            if (data.user && data.access_token) {
                setUser(data.user);
                setTokens({ access_token: data.access_token, redirect_url: data.redirect_url || '/dashboard' });

                // Dispara a atualização de parcelas em segundo plano
                fetch(`${API_BASE_URL}/cron/mark-overdue`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${data.access_token}`,
                        'X-Cron-Secret': '0f2c6ddcc8b44a6fb8e4a9dfae62e0e18ebf4fe6c7d89457b58de91f0d2d54d1',
                    },
                }).then(response => {
                    if (!response.ok && response.status !== 401) {
                        logger.warn(`Atualização automática de parcelas retornou status ${response.status}`, null, 'triggerInstallmentUpdate');
                    }
                }).catch(error => {
                    // Silenciar erro de rede, pois é uma operação em background não crítica
                });

                return data;
            } else {
                throw new Error('Resposta de autenticação inválida do servidor.');
            }
        } catch (error) {
            const errorMessage = handleApiError(error, 'login');
            // Error já logado pelo handleApiError
            throw error; // Re-lança o erro para ser tratado pelo componente de login
        }
    };

    const logout = () => {
        setUser(null);
        setTokens(null);
        navigate('/login');
    };

    const value = {
        user,
        tokens,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        setUser
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// --- Componente de Rota Protegida ---
// --- Componente de Rota Protegida ---
interface ProtectedRouteProps {
    children: React.ReactNode;
    allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
    const { user, isAuthenticated, isLoading } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return <div className="flex justify-center items-center h-screen"><p>Carregando...</p></div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (allowedRoles && user) {
        const userRole = user.role.toLowerCase();
        const hasPermission = allowedRoles.includes(userRole) || userRole === 'admin' || userRole === 'super admin';

        if (!hasPermission) {
            // Redireciona para dashboard ou mostra acesso negado
            return <Navigate to="/dashboard" replace />;
        }
    }

    return <>{children}</>;
};

// --- Tipos de Filtros ---
interface BaseFilters {
    page?: number;
    limit?: number;
    searchTerm?: string;
    showInactive?: boolean;
    category_id?: string;
}

interface SalesFilters {
    search?: string;
    status?: 'completed' | 'canceled' | '';
    payment_type?: PaymentMethod | '';
    period?: 'today' | 'week' | 'month' | 'custom' | 'all' | '';
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
}


// --- Componente principal da aplicação da Perfumaria ---
const PerfumeryApp = () => {
    const [themeColor, setThemeColor] = usePersistentState<string>('themeColor', 'purple');
    const [themeMode, setThemeMode] = usePersistentState<'light' | 'dark'>('themeMode', 'light');
    const [isSidebarOpen, setSidebarOpen] = useState(false);
    const [toasts, setToasts] = useState<{ id: number; message: string; type: 'success' | 'error' }[]>([]);

    const [products, setProducts] = usePersistentState<Product[]>('products', []);
    const [customers, setCustomers] = usePersistentState<Customer[]>('customers', []);
    const [sales, setSales] = usePersistentState<Sale[]>('sales', []);
    const [categories, setCategories] = usePersistentState<Category[]>('categories', []);
    const [installments, setInstallments] = usePersistentState<Installment[]>('installments', []);
    const [companyDetails, setCompanyDetails] = useState<Company | null>(null);

    const [totalProducts, setTotalProducts] = useState(0);
    const [totalCustomers, setTotalCustomers] = useState(0);
    const [totalSales, setTotalSales] = useState(0);
    const [totalCategories, setTotalCategories] = useState(0);
    const [totalInstallments, setTotalInstallments] = useState(0);

    const { user, tokens, logout, isAuthenticated } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    // Safety check: If we have tokens but no user, force logout to prevent broken UI
    useEffect(() => {
        if (isAuthenticated && !user) {
            logout();
        }
    }, [isAuthenticated, user, logout]);

    const chartThemeColor = useMemo(() => {
        const colorMap: { [key: string]: string } = {
            purple: '#8B5CF6',
            blue: '#3B82F6',
            green: '#22C55E',
            pink: '#EC4899',
            white: '#6B7280',
            black: '#F9FAFB'
        };
        return colorMap[themeColor] || '#8B5CF6';
    }, [themeColor]);

    useEffect(() => {
        const colors: { [key: string]: { [key: string]: string } } = {
            purple: { '50': '#F5F3FF', '100': '#EDE9FE', '300': '#C4B5FD', '600': '#7C3AED', '700': '#6D28D9' },
            blue: { '50': '#EFF6FF', '100': '#DBEAFE', '300': '#93C5FD', '600': '#2563EB', '700': '#1D4ED8' },
            green: { '50': '#F0FDF4', '100': '#DCFCE7', '300': '#86EFAC', '600': '#16A34A', '700': '#15803D' },
            pink: { '50': '#FDF2F8', '100': '#FCE7F3', '300': '#F9A8D4', '600': '#DB2777', '700': '#BE185D' },
            white: { '50': '#F9FAFB', '100': '#F3F4F6', '300': '#D1D5DB', '600': '#4B5563', '700': '#374151' },
            black: { '50': '#F8FAFC', '100': '#F1F5F9', '300': '#CBD5E1', '600': '#475569', '700': '#334155' }
        };

        const root = document.documentElement;
        const selectedPalette = colors[themeColor] || colors.purple;

        for (const [shade, color] of Object.entries(selectedPalette)) {
            root.style.setProperty(`--color-primary-${shade}`, color);
        }
    }, [themeColor]);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', themeMode === 'dark');
    }, [themeMode]);

    const toggleThemeMode = () => {
        setThemeMode(prev => (prev === 'light' ? 'dark' : 'light'));
    };

    const addToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(currentToasts => currentToasts.filter(toast => toast.id !== id));
        }, 5000);
    }, []);

    const fetchCompanyDetails = useCallback(async () => {
        if (!tokens || !user?.company_id) return;
        try {
            const response = await fetch(`${API_BASE_URL}/companies/${user.company_id}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` },
            });
            if (response.ok) {
                const data = await response.json();
                setCompanyDetails(data);
                if (data.theme_color) {
                    setThemeColor(data.theme_color);
                }
            } else {
                // Fallback to user data from token if the specific fetch fails
                setCompanyDetails({
                    id: user.company_id,
                    name: user.company_name,
                    logo_url: user.company_logo_url,
                    slug: user.company_slug,
                } as Company);
            }
        } catch (error) {
            logger.error("Failed to fetch company details", error, 'fetchCompanyDetails');
            // Fallback on error
            setCompanyDetails({
                id: user.company_id,
                name: user.company_name,
                logo_url: user.company_logo_url,
                slug: user.company_slug
            } as Company);
        }
    }, [tokens, user, API_BASE_URL, setThemeColor]);

    useEffect(() => {
        if (user && user.role.toLowerCase() !== 'admin') {
            // Se o usuário não tem company_id (Super Admin), criar objeto fictício
            if (!user.company_id) {
                setCompanyDetails({
                    id: 0,
                    name: "TatyStore",
                    logo_url: "/app-logo.png",  // Logo da plataforma (frontend public/)
                    slug: "platform",
                    cnpj: "",
                    email: "",
                    phone: "",
                    address: "",
                    is_active: true,
                    created_at: "",
                    access_url: ""
                } as Company);
            } else {
                fetchCompanyDetails();
            }
        }
    }, [fetchCompanyDetails, user]);

    const handleThemeChange = async (newColor: string) => {
        setThemeColor(newColor);

        if (tokens && user?.company_id && companyDetails) {
            try {
                const response = await fetch(`${API_BASE_URL}/companies/${user.company_id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${tokens.access_token}`,
                    },
                    body: JSON.stringify({ ...companyDetails, theme_color: newColor }),
                });

                if (!response.ok) {
                    throw new Error('Falha ao salvar a preferência de cor.');
                }
                addToast('Tema salvo com sucesso!', 'success');
            } catch (error) {
                addToast(error instanceof Error ? error.message : 'Erro ao salvar o tema.', 'error');
            }
        }
    };

    const updateCompanyDetails = async (companyData: Partial<Company>, logoFile: File | null) => {
        if (!tokens || !user?.company_id) throw new Error("Não autenticado");

        const payload: { [key: string]: any } = { ...companyData };
        if (payload.pix && typeof payload.pix === 'object') {
            payload.pix = JSON.stringify(payload.pix);
        }

        try {
            const response = await fetch(`${API_BASE_URL}/companies/${user.company_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                let errorMessage = 'Falha ao atualizar os dados da empresa.';
                if (errorData.detail && Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail.map((e: any) => `${e.loc.join('.')} - ${e.msg}`).join('; ');
                } else if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
                throw new Error(errorMessage);
            }

            if (logoFile) {
                const formData = new FormData();
                formData.append("file", logoFile);

                const logoResponse = await fetch(`${API_BASE_URL}/companies/${user.company_id}/logo`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${tokens.access_token}` },
                    body: formData,
                });

                if (!logoResponse.ok) {
                    const errorData = await logoResponse.json();
                    throw new Error(errorData.detail || 'Dados salvos, mas falha ao enviar o logo.');
                }
            }

            addToast('Empresa atualizada com sucesso!', 'success');
            await fetchCompanyDetails(); // Refresh details everywhere
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
            throw err;
        }
    };


    const fetchProducts = useCallback(async (filters: BaseFilters) => {
        if (!tokens) return;
        const params = new URLSearchParams();
        let url: string;

        if (filters.category_id) {
            url = `${API_BASE_URL}/products/by-category/${filters.category_id}`;
            params.append('skip', String(((filters.page || 1) - 1) * (filters.limit || 20)));
            params.append('limit', String(filters.limit || 20));
            if (filters.showInactive) {
                params.append('show_inactive', 'true');
            }
        } else if (filters.searchTerm) {
            url = `${API_BASE_URL}/products/search`;
            params.append('q', filters.searchTerm);
            if (filters.showInactive) {
                params.append('show_inactive', 'true');
            }
        } else {
            url = `${API_BASE_URL}/products/`;
            params.append('skip', String(((filters.page || 1) - 1) * (filters.limit || 20)));
            params.append('limit', String(filters.limit || 20));
            if (filters.showInactive) {
                params.append('show_inactive', 'true');
            }
        }

        try {
            const response = await fetch(`${url}?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` },
            });
            if (!response.ok) throw new Error('Falha ao buscar produtos.');
            const data = await response.json();

            let productsData = [];
            let total = 0;

            // Check if data is an array (e.g., search or category filter results directly returning list)
            if (Array.isArray(data)) {
                productsData = data;
                total = data.length;
            } else if (data && (data.data || data.items)) {
                // Check for paginated response structure
                productsData = data.data || data.items || [];
                total = data.metadata?.total || data.total || 0;
            } else {
                productsData = [];
                total = 0;
            }

            const parsedProducts: Product[] = productsData.map((p: any) => {
                let determinedStatus = false;
                if (typeof p.is_active === 'boolean') {
                    determinedStatus = p.is_active;
                } else if (p.status) {
                    const statusStr = String(p.status).toLowerCase();
                    determinedStatus = statusStr === 'active' || statusStr === 'ativo';
                } else {
                    // Default to active if not specified (often the case for simple lists)
                    // Or strictly follow filter logic if present
                    determinedStatus = true;
                }

                return {
                    ...p,
                    id: String(p.id),
                    is_active: determinedStatus,
                };
            });
            setProducts(parsedProducts);
            setTotalProducts(total);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido ao buscar produtos.', 'error');
        }
    }, [tokens, addToast, API_BASE_URL]);

    const fetchCustomers = useCallback(async (filters: BaseFilters) => {
        if (!tokens) return;
        const params = new URLSearchParams();
        if (filters.page) params.append('skip', String((filters.page - 1) * 20));
        if (filters.limit) params.append('limit', String(filters.limit));
        else params.append('limit', '20');
        if (filters.searchTerm) params.append('search', filters.searchTerm);
        if (filters.showInactive) params.append('show_inactive', 'true');

        try {
            const response = await fetch(`${API_BASE_URL}/customers/?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` },
            });
            if (!response.ok) throw new Error('Falha ao buscar clientes.');

            const data = await response.json();

            // Corrected: Handle both 'data' and 'items' structure
            const customersData = data.data || data.items || [];
            const total = data.metadata?.total || data.total || 0;

            const parsedCustomers: Customer[] = customersData.map((c: any) => ({
                ...c,
                id: String(c.id),
                status: c.is_active ? 'active' : 'inactive',
                total_debt: c.total_debt || 0,
            }));

            setCustomers(parsedCustomers);
            setTotalCustomers(total);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido ao buscar clientes.', 'error');
        }
    }, [tokens, addToast, API_BASE_URL]);

    const fetchSales = useCallback(async (filters: SalesFilters) => {
        if (!tokens) return;
        const params = new URLSearchParams();
        params.append('limit', String(filters.limit || 20));
        params.append('skip', String(((filters.page || 1) - 1) * (filters.limit || 20)));

        if (filters.search) params.append('search', filters.search);
        if (filters.status) params.append('status', filters.status);
        if (filters.payment_type) params.append('payment_type', filters.payment_type);
        if (filters.period && filters.period !== 'all') params.append('period', filters.period);
        if (filters.period === 'custom' && filters.start_date && filters.end_date) {
            params.append('start_date', filters.start_date);
            params.append('end_date', filters.end_date);
        }

        try {
            const response = await fetch(`${API_BASE_URL}/sales/?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Falha ao buscar vendas.');
            const data = await response.json();

            // Corrected: Handle both 'data' and 'items' structure
            const salesData = data.data || data.items || [];
            const total = data.metadata?.total || data.total || 0;

            const parsedSales: Sale[] = salesData.map((s: any) => ({
                id: String(s.id),
                customerId: String(s.customer_id),
                customerName: s.customer?.name || 'Cliente',
                items: (s.items || []).map((item: any) => ({
                    productId: String(item.product_id),
                    quantity: item.quantity,
                    unitPrice: item.unit_price,
                })),
                total: s.total_amount,
                totalCost: s.total_cost || 0,
                discountAmount: s.discount_amount || 0,
                paymentMethod: (s.payment_type || 'cash').toLowerCase() as PaymentMethod,
                installments: (s.installments || []).map((inst: any) => ({
                    id: String(inst.id),
                    saleId: String(s.id),
                    customerId: String(s.customer_id),
                    amount: inst.amount,
                    dueDate: safeParseDate(inst.due_date),
                    status: (inst.status || 'pending').toLowerCase() as InstallmentStatus,
                })),
                date: safeParseDate(s.created_at || s.sale_date),
                status: (s.status || 'completed').toLowerCase() as 'completed' | 'canceled',
            }));
            setSales(parsedSales);
            setTotalSales(total);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao buscar vendas', 'error');
        }
    }, [tokens, addToast, API_BASE_URL]);

    const fetchCategories = useCallback(async (filters: BaseFilters) => {
        if (!tokens) return;
        const params = new URLSearchParams();
        const url = `${API_BASE_URL}/categories/`;
        const isSearch = !!filters.searchTerm;

        // For a search, we fetch all categories and filter on the client.
        // For a normal view, we fetch a paginated list from the backend.
        if (isSearch) {
            params.append('limit', '1000'); // High limit to get all categories for frontend search
            params.append('show_inactive', 'true'); // Get all statuses to filter locally
        } else {
            params.append('limit', String(filters.limit || 20));
            params.append('skip', String(((filters.page || 1) - 1) * (filters.limit || 20)));
            if (filters.showInactive) {
                params.append('show_inactive', 'true');
            }
        }

        try {
            const response = await fetch(`${url}?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Falha ao buscar categorias.');
            const data = await response.json();

            // Corrected: Handle both 'data' and 'items' structure
            let categoriesData = data.data || data.items || [];
            let total = data.metadata?.total || data.total || 0;

            // If a search was performed, filter the full list on the client-side
            if (isSearch && filters.searchTerm) {
                const lowercasedTerm = filters.searchTerm.toLowerCase();
                categoriesData = categoriesData.filter((cat: Category) =>
                    cat.name.toLowerCase().includes(lowercasedTerm) ||
                    (cat.description && cat.description.toLowerCase().includes(lowercasedTerm))
                );

                // Also filter by activity status if the user doesn't want to see inactive ones
                if (!filters.showInactive) {
                    categoriesData = categoriesData.filter((cat: Category) => cat.is_active);
                }

                // When searching, the total is the count of filtered items, as there's no pagination.
                total = categoriesData.length;
            }

            setCategories(categoriesData);
            setTotalCategories(total);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao buscar categorias.', 'error');
        }
    }, [tokens, addToast, API_BASE_URL]);

    const fetchInstallments = useCallback(async (filters: { search?: string; customer_id?: string; status_filter?: InstallmentStatus | ''; page?: number; limit?: number }) => {
        if (!tokens) return;
        const params = new URLSearchParams();
        params.append('limit', String(filters.limit || 20));
        params.append('skip', String(((filters.page || 1) - 1) * (filters.limit || 20)));

        let url: string;

        if (filters.status_filter === 'overdue') {
            url = `${API_BASE_URL}/installments/overdue`;
        } else {
            url = `${API_BASE_URL}/installments/`;
            if (filters.status_filter) {
                params.append('status_filter', filters.status_filter);
            }
        }

        if (filters.customer_id) params.append('customer_id', filters.customer_id);
        if (filters.search) params.append('search', filters.search);

        try {
            const response = await fetch(`${url}?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Falha ao buscar parcelas.');
            const data = await response.json();

            // Corrected: Handle both 'data' and 'items' structure
            const installmentsData = data.data || data.items || [];
            const total = data.metadata?.total || data.total || 0;

            const parsedInstallments: Installment[] = installmentsData.map((inst: any) => ({
                id: String(inst.id),
                saleId: String(inst.sale_id),
                customerId: String(inst.customer_id),
                amount: inst.amount,
                dueDate: safeParseDate(inst.due_date),
                status: (inst.status || 'pending').toLowerCase() as InstallmentStatus,
                customerName: inst.customer?.name || 'Cliente não identificado', // Explicitly map customer name from nested object
                saleDate: safeParseDate(inst.created_at),
                remainingAmount: inst.remaining_amount // Map the remaining amount
            }));
            setInstallments(parsedInstallments);
            setTotalInstallments(total);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao buscar parcelas', 'error');
        }
    }, [tokens, addToast, API_BASE_URL]);

    const addSale = async (saleData: Omit<Sale, 'id' | 'installments' | 'status' | 'date' | 'total' | 'totalCost'> & { numInstallments?: number }) => {
        if (!tokens) throw new Error("Não autenticado");

        const itemsPayload = saleData.items.map(item => {
            if (typeof item.unitPrice !== 'number' || isNaN(item.unitPrice)) {
                const errorMessage = `O produto "${item.productName || item.productId}" está com preço inválido. A venda não pode ser finalizada.`;
                addToast(errorMessage, 'error');
                throw new Error(errorMessage);
            }
            return {
                product_id: item.productId,
                quantity: item.quantity,
                unit_price: item.unitPrice,
                unit_cost_price: item.unitCostPrice
            };
        });

        const salePayload = {
            customer_id: saleData.customerId,
            items: itemsPayload,
            payment_type: saleData.paymentMethod,
            discount_amount: saleData.discountAmount,
            installments_count: saleData.numInstallments,
            first_due_date: saleData.firstDueDate?.toISOString().split('T')[0]
        };

        const response = await fetch(`${API_BASE_URL}/sales/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${tokens.access_token}`,
            },
            body: JSON.stringify(salePayload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Falha ao registrar a venda.');
        }

        const newSale = await response.json();
        addToast('Venda registrada com sucesso!');
        await fetchSales({ page: 1 });
        await fetchProducts({ page: 1, showInactive: true });
        return newSale;
    };

    const cancelSale = async (saleId: string) => {
        if (!tokens) return;
        try {
            const response = await fetch(`${API_BASE_URL}/sales/${saleId}/cancel`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${tokens.access_token}` },
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Falha ao cancelar a venda.' }));
                throw new Error(errorData.detail);
            }
            addToast('Venda cancelada com sucesso!');
            await fetchSales({ page: 1 });
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao cancelar', 'error');
        }
    };

    useEffect(() => {
        if (tokens && user && user.role.toLowerCase() !== 'admin') {
            fetchProducts({ page: 1, showInactive: true });
            fetchCustomers({ page: 1, showInactive: true });
            fetchSales({ page: 1 });
            fetchCategories({ showInactive: true });
            fetchInstallments({ page: 1 });
        }
    }, [tokens, user]);

    const pageTitle = useMemo(() => {
        const path = location.pathname.split('/')[1];
        const titles: { [key: string]: string } = {
            dashboard: 'Dashboard',
            products: 'Estoque',
            sales: 'Vendas',
            installments: 'Parcelas',
            customers: 'Clientes',
            reports: 'Relatórios',
            settings: 'Configurações',
            company: 'Minha Empresa',
            users: 'Usuários',
            categories: 'Categorias',
            profile: 'Perfil'
        };
        // Special case for admin
        if (user?.role.toLowerCase() === 'admin' && path === 'dashboard') {
            return 'Empresas';
        }
        if (user?.role.toLowerCase() === 'admin' && path === '') {
            return 'Empresas';
        }
        return titles[path] || 'Taty Store';
    }, [location.pathname, user]);

    // Admin Redirect
    useEffect(() => {
        if (user?.role.toLowerCase() === 'admin' && location.pathname === '/dashboard') {
            navigate('/companies', { replace: true });
        }
    }, [user, location.pathname, navigate]);

    return (
        <div className="flex h-[100dvh] bg-gray-50 dark:bg-gray-900">
            <ToastContainer toasts={toasts} />
            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setSidebarOpen(false)}
                themeColor={themeColor}
                user={user}
                company={companyDetails}
                serverUrl={SERVER_BASE_URL}
            />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header
                    onMenuClick={() => setSidebarOpen(true)}
                    pageTitle={pageTitle}
                    user={user}
                    themeColor={themeColor}
                    company={companyDetails}
                    serverUrl={SERVER_BASE_URL}
                />
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900 p-4 sm:p-6">
                    <Outlet context={{
                        products,
                        totalProducts,
                        fetchProducts,
                        customers,
                        totalCustomers,
                        fetchCustomers,
                        sales,
                        totalSales,
                        fetchSales,
                        installments,
                        totalInstallments,
                        fetchInstallments,
                        categories,
                        totalCategories,
                        fetchCategories,
                        addSale,
                        cancelSale,
                        addToast,
                        themeColor,
                        setThemeColor: handleThemeChange,
                        themeMode,
                        toggleThemeMode,
                        chartThemeColor,
                        user,
                        companyDetails,
                        updateCompanyDetails,
                        serverUrl: SERVER_BASE_URL,
                        apiUrl: API_BASE_URL
                    }} />
                </main>
            </div>
        </div>
    );
};

const PublicLayout = () => {
    const [toasts, setToasts] = useState<{ id: number; message: string; type: 'success' | 'error' }[]>([]);

    return (
        <div className="bg-gray-100 dark:bg-gray-900 min-h-[100dvh]">
            <ToastContainer toasts={toasts} />
            <Outlet />
        </div>
    );
};

const App = () => {
    return (
        <AuthProvider>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />

                <Route path="/store/:companySlug" element={<PublicLayout />}>
                    <Route index element={<StorefrontPage />} />
                    <Route path="products/:productId" element={<ProductDetailPage />} />
                </Route>

                <Route
                    element={
                        <ProtectedRoute>
                            <PerfumeryApp />
                        </ProtectedRoute>
                    }
                >
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="products/import" element={<ProductImport />} />
                    <Route path="products" element={<Products />} />
                    <Route path="products/:productId" element={<Products />} />
                    <Route path="sales" element={<Sales />} />
                    <Route path="sales/:saleId" element={<Sales />} />
                    <Route path="customers" element={<Customers />} />
                    <Route path="customers/:customerId" element={<Customers />} />
                    <Route path="installments" element={<InstallmentsPage />} />
                    <Route path="installments/payment/:installmentId" element={<InstallmentsPage />} />
                    <Route path="users/*" element={
                        <ProtectedRoute allowedRoles={['gerente']}>
                            <UsersPage />
                        </ProtectedRoute>
                    } />
                    <Route path="users/:userId" element={
                        <ProtectedRoute allowedRoles={['gerente']}>
                            <UsersPage />
                        </ProtectedRoute>
                    } />
                    <Route path="reports" element={
                        <ProtectedRoute allowedRoles={['gerente']}>
                            <Reports />
                        </ProtectedRoute>
                    } />
                    <Route path="settings" element={
                        <ProtectedRoute allowedRoles={['gerente']}>
                            <Settings />
                        </ProtectedRoute>
                    } />
                    <Route path="company" element={
                        <ProtectedRoute allowedRoles={['gerente']}>
                            <CompanyPage />
                        </ProtectedRoute>
                    } />
                    <Route path="companies" element={
                        <ProtectedRoute allowedRoles={['admin']}>
                            <CompaniesPage />
                        </ProtectedRoute>
                    } />
                    <Route path="companies/:companyId" element={<CompaniesPage />} />
                    <Route path="categories" element={<CategoriesPage />} />
                    <Route path="categories/:categoryId" element={<CategoriesPage />} />
                    <Route path="profile" element={<Profile />} />
                    {/* Fallback route within protected area */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Route>
            </Routes>
        </AuthProvider>
    );
};

export default App;
