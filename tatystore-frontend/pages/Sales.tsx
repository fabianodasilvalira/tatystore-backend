
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { useOutletContext, useParams, useNavigate, useLocation } from 'react-router-dom';
import { Sale, Product, Customer, PaymentMethod, SaleItem, Installment, User, Category, Company, InstallmentStatus } from '../types';
import InstallmentStatusBadge from '../components/InstallmentStatusBadge';
import PaymentBooklet from '../components/PaymentBooklet';
import { useAuth } from '../App';
import Pagination from '../components/Pagination';
import { safeParseDate } from '../utils/dateUtils';

interface SalesContext {
    sales: Sale[];
    products: Product[];
    customers: Customer[];
    categories: Category[];
    addSale: (sale: Omit<Sale, 'id' | 'installments' | 'status' | 'date' | 'total' | 'totalCost'> & { numInstallments?: number }) => Promise<Sale>;
    cancelSale: (saleId: string) => void;
    addToast: (message: string, type?: 'success' | 'error') => void;
    user: User | null;
    fetchSales: (filters: any) => Promise<void>;
    totalSales: number;
    fetchCustomers: (filters: any) => Promise<void>;
    fetchProducts: (filters: any) => Promise<void>;
    apiUrl: string;
    companyDetails: Company | null;
}

// safeParseDate agora importado de utils/dateUtils.ts

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);

const Sales: React.FC = () => {
    const { sales, products, customers, categories, addSale, cancelSale, addToast, user, fetchSales, totalSales, fetchCustomers, fetchProducts, apiUrl, companyDetails } = useOutletContext<SalesContext>();
    const { saleId } = useParams<{ saleId: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { tokens } = useAuth();

    const isManager = useMemo(() => user?.role?.toLowerCase() === 'gerente', [user]);

    const isNewView = location.pathname === '/sales/new';
    const isDetailsView = !!(saleId && !isNewView);

    const [detailedSale, setDetailedSale] = useState<Sale | null>(null);
    const [saleCustomer, setSaleCustomer] = useState<Customer | null>(null);
    const [isDetailLoading, setIsDetailLoading] = useState(false);

    const [showBooklet, setShowBooklet] = useState(false);

    const initialSaleState = {
        customerId: '',
        items: [] as (Omit<SaleItem, 'unitCostPrice'> & { name: string; unitCostPrice: number; originalUnitPrice?: number })[],
        paymentMethod: 'cash' as PaymentMethod,
        discountAmount: '',
        numInstallments: '1',
        firstDueDate: new Date()
    };

    const [newSale, setNewSale] = useState(initialSaleState);
    const [currentItem, setCurrentItem] = useState<{ product: Product | null, quantity: number }>({ product: null, quantity: 1 });
    const [productSearchTerm, setProductSearchTerm] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('');
    const [productSearchResults, setProductSearchResults] = useState<Product[]>([]);
    const [isSearchingProducts, setIsSearchingProducts] = useState(false);
    const [isProductSearchFocused, setIsProductSearchFocused] = useState(false);
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [saleToCancelId, setSaleToCancelId] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Customer Search State
    const [customerSearch, setCustomerSearch] = useState('');
    const [isCustomerDropdownOpen, setIsCustomerDropdownOpen] = useState(false);

    const initialFiltersState = {
        search: '',
        status: '',
        payment_type: '' as PaymentMethod | '',
        period: 'all',
        start_date: '',
        end_date: '',
    };
    const [filters, setFilters] = useState(initialFiltersState);
    const [searchTerm, setSearchTerm] = useState('');

    const [currentPage, setCurrentPage] = useState(1);
    const [isLoading, setIsLoading] = useState(true);
    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil((totalSales || 0) / ITEMS_PER_PAGE), [totalSales]);

    const paymentMethodInfo: { [key in PaymentMethod]: { text: string; icon: string; color: string } } = {
        cash: { text: 'À vista', icon: 'payments', color: 'text-blue-600 dark:text-blue-400' },
        credit: { text: 'Crediário', icon: 'credit_card', color: 'text-orange-600 dark:text-orange-400' },
        pix: { text: 'PIX', icon: 'qr_code_2', color: 'text-green-600 dark:text-green-400' },
    };

    const fetchSaleDetails = useCallback(async (id: string) => {
        if (!tokens) return;
        setIsDetailLoading(true);
        try {
            const response = await fetch(`${apiUrl}/sales/${id}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    addToast('Venda não encontrada.', 'error');
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Falha ao carregar detalhes da venda.');
                }
                navigate('/sales', { replace: true });
                return;
            }

            const saleData = await response.json();

            const parsedSale: Sale = {
                id: String(saleData.id),
                customerId: String(saleData.customer_id),
                customerName: saleData.customer?.name || 'Cliente Desconhecido',
                items: (saleData.items || []).map((item: any): SaleItem => ({
                    productId: String(item.product_id),
                    quantity: item.quantity,
                    unitPrice: item.unit_price,
                    unitCostPrice: item.unit_cost_price || 0,
                    productName: item.product?.name || 'Produto Desconhecido',
                })),
                total: saleData.total_amount,
                totalCost: saleData.total_cost || 0,
                profit: saleData.profit,
                profit_margin_percentage: saleData.profit_margin_percentage,
                discountAmount: saleData.discount_amount,
                paymentMethod: (saleData.payment_type || '').toLowerCase() as PaymentMethod,
                installments: (saleData.installments || []).map((inst: any): Installment => ({
                    id: String(inst.id),
                    saleId: String(saleData.id),
                    customerId: String(saleData.customer_id),
                    amount: inst.amount,
                    dueDate: safeParseDate(inst.due_date),
                    status: (inst.status || '').toLowerCase() as InstallmentStatus,
                    remainingAmount: inst.remaining_amount // Map the remaining amount
                })),
                date: safeParseDate(saleData.created_at || saleData.sale_date),
                firstDueDate: saleData.first_due_date ? safeParseDate(saleData.first_due_date) : undefined,
                status: (saleData.status || '').toLowerCase() as 'completed' | 'canceled',
            };

            setDetailedSale(parsedSale);

            if (saleData.customer) {
                const parsedCustomer: Customer = {
                    ...saleData.customer,
                    id: String(saleData.customer.id),
                    status: saleData.customer.is_active ? 'active' : 'inactive',
                    total_debt: saleData.customer.total_debt || 0
                };
                setSaleCustomer(parsedCustomer);
            }

        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao buscar venda', 'error');
            navigate('/sales', { replace: true });
        } finally {
            setIsDetailLoading(false);
        }
    }, [tokens, addToast, navigate, apiUrl]);

    useEffect(() => {
        if (isDetailsView && saleId) {
            fetchSaleDetails(saleId);
        }
    }, [isDetailsView, saleId, fetchSaleDetails]);

    // Reset state when visiting root path
    useEffect(() => {
        if (location.pathname === '/sales') {
            setSearchTerm('');
            setFilters(initialFiltersState);
            setCurrentPage(1);
        }
    }, [location.pathname]);

    useEffect(() => {
        // Fetch customers for the new sale form
        fetchCustomers({ limit: 1000, showInactive: false });
    }, [fetchCustomers]);


    const salesWithDetails = useMemo(() => {
        return sales.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }, [sales]);

    const handleAddItem = () => {
        if (!currentItem.product || currentItem.quantity <= 0) return;

        const { product, quantity } = currentItem;

        const isPromo = product.is_on_sale && product.promotional_price && product.promotional_price > 0;
        const unitPrice = isPromo ? product.promotional_price! : product.sale_price;
        const originalUnitPrice = isPromo ? product.sale_price : undefined;

        setNewSale(prev => ({
            ...prev,
            items: [...prev.items, {
                productId: product.id,
                quantity,
                unitPrice,
                originalUnitPrice,
                unitCostPrice: product.cost_price,
                name: product.name
            }]
        }));
        setCurrentItem({ product: null, quantity: 1 });
        setProductSearchTerm('');
        setProductSearchResults([]);
        setErrors(prev => ({ ...prev, items: '' }));
    };

    const searchProducts = useCallback(async (query: string, categoryId: string) => {
        if (!tokens) return;
        setIsSearchingProducts(true);
        try {
            const params = new URLSearchParams();
            params.append('show_inactive', 'false');
            params.append('limit', '100');

            let url: string;

            if (categoryId) {
                url = `${apiUrl}/products/by-category/${categoryId}`;
            } else if (query) {
                url = `${apiUrl}/products/search`;
                params.append('q', encodeURIComponent(query));
            } else {
                url = `${apiUrl}/products/`;
            }

            const response = await fetch(`${url}?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });

            if (!response.ok) throw new Error('Falha ao buscar produtos.');
            const data = await response.json();

            const productsData = Array.isArray(data) ? data : (data.data || []);

            const parsedProducts = productsData.map((product: any) => {
                const salePriceValue = product.price ?? product.sale_price;
                const promotionalPriceValue = product.promotional_price;

                const salePrice = salePriceValue ? parseFloat(String(salePriceValue)) : 0;
                const promotionalPrice = promotionalPriceValue ? parseFloat(String(promotionalPriceValue)) : null;

                let determinedStatus = false;
                if (typeof product.is_active === 'boolean') {
                    determinedStatus = product.is_active;
                } else if (product.status) {
                    const statusStr = String(product.status).toLowerCase();
                    determinedStatus = statusStr === 'active' || statusStr === 'ativo';
                } else {
                    determinedStatus = true;
                }

                return {
                    ...product,
                    id: String(product.id),
                    sale_price: isNaN(salePrice) ? 0 : salePrice,
                    promotional_price: promotionalPrice === null || isNaN(promotionalPrice) ? null : promotionalPrice,
                    is_active: determinedStatus,
                };
            });
            setProductSearchResults(parsedProducts);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro na busca de produtos.', 'error');
            setProductSearchResults([]);
        } finally {
            setIsSearchingProducts(false);
        }
    }, [tokens, addToast, apiUrl]);

    const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newCategoryId = e.target.value;
        setCategoryFilter(newCategoryId);
        setProductSearchTerm('');
        setCurrentItem({ product: null, quantity: 1 });
        setProductSearchResults([]);
    };

    // Effect to handle initial product load for new sale form
    useEffect(() => {
        if (isNewView) {
            setProductSearchTerm('');
            setCategoryFilter('');
        }
    }, [isNewView]);

    // Effect to handle debounced search/filter
    useEffect(() => {
        if (!isNewView) return;

        const timer = setTimeout(() => {
            searchProducts(productSearchTerm, categoryFilter);
        }, 300);

        return () => clearTimeout(timer);
    }, [isNewView, productSearchTerm, categoryFilter, searchProducts]);


    const handleRemoveItem = (productId: string) => {
        setNewSale(prev => ({
            ...prev,
            items: prev.items.filter(item => item.productId !== productId)
        }));
    };

    const totalNewSale = newSale.items.reduce((sum, item) => sum + (item.unitPrice * item.quantity), 0);
    const numericDiscount = parseFloat(String(newSale.discountAmount).replace(',', '.')) || 0;
    const itemsInCartIds = useMemo(() => new Set(newSale.items.map(item => item.productId)), [newSale.items]);

    const handleSelectProduct = async (product: Product) => {
        if (!tokens) return;
        try {
            // Fetch the most up-to-date product details to ensure price is correct
            const response = await fetch(`${apiUrl}/products/${product.id}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Não foi possível obter os dados atualizados do produto.');

            const freshProductData = await response.json();
            setCurrentItem({ product: freshProductData, quantity: 1 });
            setProductSearchTerm(freshProductData.name);
            setIsProductSearchFocused(false);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro ao selecionar produto.', 'error');
        }
    };

    const validateSaleForm = () => {
        const newErrors: { [key: string]: string } = {};
        const parsedInstallments = parseInt(String(newSale.numInstallments), 10);

        if (!newSale.customerId) newErrors.customerId = "É obrigatório selecionar um cliente.";
        if (newSale.items.length === 0) newErrors.items = "Adicione pelo menos um item à venda.";
        if (newSale.paymentMethod === 'credit' && (isNaN(parsedInstallments) || parsedInstallments < 1 || parsedInstallments > 60)) {
            newErrors.numInstallments = "O número de parcelas deve ser entre 1 e 60.";
        }
        if (numericDiscount > totalNewSale) newErrors.discountAmount = "O desconto não pode ser maior que o subtotal.";

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSubmitting || !validateSaleForm()) {
            return;
        }
        setIsSubmitting(true);

        const saleDataForApp = {
            customerId: newSale.customerId,
            items: newSale.items.map(({ name, unitCostPrice, originalUnitPrice, ...rest }) => ({ ...rest, unitCostPrice })),
            paymentMethod: newSale.paymentMethod,
            discountAmount: numericDiscount,
            numInstallments: newSale.paymentMethod === 'credit' ? (parseInt(String(newSale.numInstallments), 10) || 1) : undefined,
            firstDueDate: newSale.paymentMethod === 'credit' ? newSale.firstDueDate : undefined,
        };

        try {
            const completedSale = await addSale(saleDataForApp);
            setNewSale(initialSaleState);
            setErrors({});
            navigate(`/sales/${completedSale.id}`);
        } catch (error) {
            addToast(error instanceof Error ? error.message : "Erro desconhecido", 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancelSale = (saleId: string) => {
        setSaleToCancelId(saleId);
    };

    const confirmCancellation = () => {
        if (saleToCancelId) {
            cancelSale(saleToCancelId);
        }
        setSaleToCancelId(null);
        navigate('/sales');
    };

    const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
        const { name, value } = e.target;
        setCurrentPage(1);
        setFilters(prev => ({ ...prev, [name]: value as any }));
    };

    const handlePageChange = (page: number) => {
        if (page > 0 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    useEffect(() => {
        const handler = setTimeout(() => {
            setCurrentPage(1);
            setFilters(f => ({ ...f, search: searchTerm }));
        }, 500);

        return () => {
            clearTimeout(handler);
        };
    }, [searchTerm]);

    useEffect(() => {
        if (isNewView || isDetailsView) {
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        fetchSales({
            ...filters,
            page: currentPage,
            limit: ITEMS_PER_PAGE
        }).finally(() => {
            setIsLoading(false);
        });

    }, [currentPage, filters, isNewView, isDetailsView, fetchSales]);

    const selectedCustomer = useMemo(() => customers.find(c => c.id === newSale.customerId), [customers, newSale.customerId]);

    const filteredCustomers = useMemo(() => {
        if (!customerSearch) return customers.filter(c => c.is_active);
        return customers.filter(c =>
            c.is_active && c.name.toLowerCase().includes(customerSearch.toLowerCase())
        );
    }, [customerSearch, customers]);

    const handleCustomerSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setCustomerSearch(value);
        setIsCustomerDropdownOpen(true);
        if (newSale.customerId) {
            setNewSale(prev => ({ ...prev, customerId: '' }));
        }
    };

    const handleCustomerSearchFocus = () => {
        setIsCustomerDropdownOpen(true);
        setCustomerSearch('');
        if (newSale.customerId) {
            setNewSale(prev => ({ ...prev, customerId: '' }));
        }
    };

    const handleCustomerSelect = (customer: Customer) => {
        setNewSale(prev => ({ ...prev, customerId: customer.id }));
        setCustomerSearch(customer.name);
        setIsCustomerDropdownOpen(false);
    };

    useEffect(() => {
        if (selectedCustomer && customerSearch !== selectedCustomer.name) {
            setCustomerSearch(selectedCustomer.name);
        }
    }, [selectedCustomer, customerSearch]);


    if (saleToCancelId) {
        return (
            <div>
                <BackButton onClick={() => setSaleToCancelId(null)} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar Cancelamento</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">Tem certeza que deseja cancelar esta venda? O estoque dos produtos será devolvido.</p>
                    <div className="flex justify-center gap-4">
                        <button onClick={() => setSaleToCancelId(null)} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors">Não</button>
                        <button onClick={confirmCancellation} className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-6 rounded-lg transition-colors">Sim, Cancelar Venda</button>
                    </div>
                </div>
            </div>
        );
    }

    if (isDetailsView) {
        if (isDetailLoading) {
            return (
                <div>
                    <BackButton onClick={() => navigate(-1)} />
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                        <p className="text-gray-500 dark:text-gray-400">Carregando detalhes da venda...</p>
                    </div>
                </div>
            );
        }

        if (!detailedSale) {
            return (
                <div>
                    <BackButton onClick={() => navigate(-1)} />
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                        <h1 className="text-2xl font-bold text-red-500">Venda não encontrada</h1>
                        <p className="text-gray-600 dark:text-gray-300 mt-2">A venda que você está procurando não existe ou foi removida.</p>
                    </div>
                </div>
            );
        }

        const customer = saleCustomer;

        const handleSendPurchaseSummary = () => {
            if (!customer || !detailedSale) return;
            const phone = customer.phone.replace(/\D/g, '');
            let message = `Olá, ${customer.name}!\n\n`;

            if (detailedSale.status === 'canceled') {
                message += `Referente à sua compra do dia ${new Date(detailedSale.date).toLocaleDateString('pt-BR')}, informamos que ela foi *CANCELADA*.\n\n`;
                message += 'Itens da compra:\n';
            } else {
                message += `Obrigado pela sua compra em nossa loja, realizada em ${new Date(detailedSale.date).toLocaleDateString('pt-BR')}.\n\n`;
                message += '*Resumo da Compra:*\n';
            }

            detailedSale.items.forEach(item => {
                message += `- ${item.quantity}x ${item.productName || 'Produto desconhecido'}\n`;
            });

            if (detailedSale.discountAmount > 0) {
                const subtotal = detailedSale.total + detailedSale.discountAmount;
                message += `\nSubtotal: ${formatCurrency(subtotal)}\n`;
                message += `Desconto: -${formatCurrency(detailedSale.discountAmount)}\n`;
            }
            message += `*Total: ${formatCurrency(detailedSale.total)}*\n\n`;

            if (detailedSale.paymentMethod === 'credit' && detailedSale.installments.length > 0 && detailedSale.status === 'completed') {
                message += '*Detalhes do Parcelamento:*\n';
                detailedSale.installments.forEach((inst, index) => {
                    const dueDate = inst.dueDate;
                    const formattedDate = !isNaN(dueDate.getTime()) ? dueDate.toLocaleDateString('pt-BR') : 'Data inválida';

                    // Use remaining amount logic here
                    const remaining = inst.remainingAmount !== undefined ? inst.remainingAmount : inst.amount;
                    const isPaid = inst.status === 'paid';
                    const isPartial = remaining > 0 && remaining < inst.amount;

                    let statusText = '';
                    if (isPaid) statusText = ' (Pago)';
                    else if (isPartial) statusText = ` (Restam: ${formatCurrency(remaining)})`;

                    message += `Parcela ${index + 1}/${detailedSale.installments.length}: ${formatCurrency(inst.amount)}${statusText} - Vencimento: ${formattedDate}\n`;
                });
                message += '\nAgradecemos a preferência!';
            } else if (detailedSale.status === 'canceled') {
                message += 'Para mais detalhes, entre em contato com a loja.';
            }
            else {
                message += 'Agradecemos a preferência!';
            }

            const whatsappUrl = `https://wa.me/55${phone}?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        };

        return (
            <>
                {showBooklet && customer && companyDetails && (
                    <PaymentBooklet
                        sale={detailedSale}
                        customer={customer}
                        company={companyDetails}
                        onClose={() => setShowBooklet(false)}
                    />
                )}
                <div>
                    <BackButton onClick={() => navigate(-1)} />
                    <div className={`p-6 rounded-2xl shadow-md ${detailedSale.status === 'canceled' ? 'bg-red-50/50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' : 'bg-white dark:bg-gray-800'}`}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-4">
                                <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Detalhes da Venda</h1>
                                <span className={`px-3 py-1.5 rounded-full text-sm font-semibold ${detailedSale.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                    {detailedSale.status === 'completed' ? 'Finalizada' : 'Cancelada'}
                                </span>
                            </div>
                            <div className="text-right">
                                {isManager && detailedSale.status === 'completed' && typeof detailedSale.profit === 'number' && (
                                    <div>
                                        <p className="font-semibold text-lg text-green-600 dark:text-green-400">
                                            Lucro: {formatCurrency(detailedSale.profit)}
                                        </p>
                                        {typeof detailedSale.profit_margin_percentage === 'number' && (
                                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                                Margem: {detailedSale.profit_margin_percentage.toFixed(2)}%
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="space-y-4">
                            {customer && (
                                <div>
                                    <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100">{customer.name}</h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">{customer.phone}</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Data da Compra: {!isNaN(detailedSale.date.getTime()) ? detailedSale.date.toLocaleDateString('pt-BR') : 'Data inválida'}</p>
                                </div>
                            )}
                            <div className="border-t dark:border-gray-700 pt-4">
                                <h4 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">Itens</h4>
                                <ul className="divide-y dark:divide-gray-700">
                                    {detailedSale.items.map(item => {
                                        return (
                                            <li key={item.productId} className="flex justify-between py-2">
                                                <div>
                                                    <p className="font-medium text-gray-800 dark:text-gray-200">{item.productName || 'Produto'}</p>
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">{item.quantity} x {formatCurrency(item.unitPrice)}</p>
                                                </div>
                                                <p className="font-semibold text-gray-800 dark:text-gray-200">{formatCurrency(item.quantity * item.unitPrice)}</p>
                                            </li>
                                        )
                                    })}
                                </ul>
                                {detailedSale.discountAmount > 0 && (
                                    <div className="flex justify-end font-semibold text-lg mt-2 py-2 text-red-500 dark:text-red-400">
                                        <span>Desconto:</span>
                                        <span className="ml-2">- {formatCurrency(detailedSale.discountAmount)}</span>
                                    </div>
                                )}
                                <div className="flex justify-end font-bold text-xl mt-2 py-2 border-t dark:border-gray-700 text-gray-800 dark:text-gray-100">
                                    <span>Total:</span>
                                    <span className="ml-2">{formatCurrency(detailedSale.total)}</span>
                                </div>
                            </div>

                            {detailedSale.paymentMethod === 'credit' && detailedSale.installments.length > 0 && (
                                <div className="border-t dark:border-gray-700 pt-4">
                                    <h4 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">Parcelamento</h4>
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-gray-100 dark:bg-gray-700">
                                            <tr>
                                                <th className="p-2 font-semibold text-gray-600 dark:text-gray-300">#</th>
                                                <th className="p-2 font-semibold text-gray-600 dark:text-gray-300">Vencimento</th>
                                                <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-right">Valor</th>
                                                <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-right">Restante</th>
                                                <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {detailedSale.installments.map((inst, index) => {
                                                const dueDate = inst.dueDate;
                                                const formattedDate = !isNaN(dueDate.getTime()) ? dueDate.toLocaleDateString('pt-BR') : 'Inválida';
                                                const remaining = inst.remainingAmount !== undefined ? inst.remainingAmount : inst.amount;
                                                const showRemaining = inst.status !== 'paid' && remaining < inst.amount;

                                                return (
                                                    <tr key={inst.id} className="border-t dark:border-gray-700">
                                                        <td className="p-2 font-medium text-gray-800 dark:text-gray-200">{`${index + 1}/${detailedSale.installments.length}`}</td>
                                                        <td className="p-2 text-gray-800 dark:text-gray-200">{formattedDate}</td>
                                                        <td className="p-2 text-right font-medium text-gray-800 dark:text-gray-200">{formatCurrency(inst.amount)}</td>
                                                        <td className="p-2 text-right font-bold text-red-600 dark:text-red-400">
                                                            {inst.status === 'paid' ? '-' : formatCurrency(remaining)}
                                                        </td>
                                                        <td className="p-2 text-center">
                                                            <InstallmentStatusBadge status={inst.status} />
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                        <div className="flex flex-col sm:flex-row justify-end items-stretch sm:items-center mt-6 pt-4 border-t dark:border-gray-700 gap-4">
                            {detailedSale.paymentMethod === 'credit' && detailedSale.status === 'completed' && (
                                <button
                                    onClick={() => setShowBooklet(true)}
                                    className="flex items-center justify-center bg-blue-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-blue-600 transition-colors"
                                >
                                    <span className="material-symbols-outlined mr-2">receipt_long</span>
                                    Gerar Carnê
                                </button>
                            )}
                            <button
                                onClick={handleSendPurchaseSummary}
                                className="flex items-center justify-center bg-green-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-green-600 transition-colors"
                            >
                                <span className="material-symbols-outlined mr-2">share</span>
                                Enviar Resumo
                            </button>
                            {isManager && detailedSale.status === 'completed' && (
                                <button
                                    onClick={() => handleCancelSale(detailedSale.id)}
                                    className="flex items-center justify-center bg-red-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-red-600 transition-colors"
                                >
                                    <span className="material-symbols-outlined mr-2">cancel</span>
                                    Cancelar Venda
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </>
        )
    }

    if (isNewView) {
        return (
            <div>
                <BackButton onClick={() => navigate('/sales')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Registrar Nova Venda</h1>
                    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                        <div>
                            <div className="relative">
                                <label className="block font-medium dark:text-gray-300 mb-1">Cliente</label>
                                <input
                                    type="text"
                                    placeholder="Digite para buscar ou clique para ver todos"
                                    value={customerSearch}
                                    onChange={handleCustomerSearchChange}
                                    onFocus={handleCustomerSearchFocus}
                                    onBlur={() => setTimeout(() => setIsCustomerDropdownOpen(false), 200)}
                                    required
                                    className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.customerId ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                                />
                                {isCustomerDropdownOpen && (
                                    <ul className="absolute z-50 w-full bg-white dark:bg-gray-800 border dark:border-gray-600 shadow-lg rounded-md mt-1 max-h-60 overflow-y-auto">
                                        {filteredCustomers.length > 0 ? (
                                            filteredCustomers.map(c => (
                                                <li
                                                    key={c.id}
                                                    className="p-3 hover:bg-primary-50 dark:hover:bg-primary-700/20 cursor-pointer text-gray-800 dark:text-gray-200"
                                                    onMouseDown={() => handleCustomerSelect(c)}
                                                >
                                                    {c.name}
                                                </li>
                                            ))
                                        ) : (
                                            <li className="p-3 text-gray-500 dark:text-gray-400">Nenhum cliente encontrado.</li>
                                        )}
                                    </ul>
                                )}
                                {errors.customerId && <p className="text-red-500 text-xs mt-1">{errors.customerId}</p>}
                            </div>

                            <div className="border dark:border-gray-700 p-4 rounded-lg space-y-2 mt-4">
                                <h3 className="font-bold text-gray-800 dark:text-gray-200">Itens da Venda</h3>
                                <div className="flex flex-col sm:flex-row gap-2 items-end">
                                    <div className="w-full sm:w-48">
                                        <label className="block font-medium dark:text-gray-300 mb-1 text-sm">Categoria</label>
                                        <select
                                            value={categoryFilter}
                                            onChange={handleCategoryChange}
                                            className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                                        >
                                            <option value="">Todas</option>
                                            {categories.filter(c => c.is_active).map(cat => (
                                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="flex-1 w-full relative">
                                        <label className="block font-medium dark:text-gray-300 mb-1 text-sm">Produto</label>
                                        <div className="relative">
                                            <input
                                                type="text"
                                                placeholder="Busque por nome, marca..."
                                                value={productSearchTerm}
                                                onChange={e => {
                                                    setProductSearchTerm(e.target.value);
                                                    if (categoryFilter) setCategoryFilter('');
                                                    if (currentItem.product) setCurrentItem(prev => ({ ...prev, product: null }));
                                                }}
                                                onFocus={() => setIsProductSearchFocused(true)}
                                                onBlur={() => setTimeout(() => setIsProductSearchFocused(false), 200)}
                                                className="w-full p-2 pr-10 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                                            />
                                            {productSearchTerm && (
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setProductSearchTerm('');
                                                        setCurrentItem(p => ({ ...p, product: null }));
                                                    }}
                                                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                                    aria-label="Limpar busca de produto"
                                                >
                                                    <span className="material-symbols-outlined">close</span>
                                                </button>
                                            )}
                                        </div>
                                        {isProductSearchFocused && (
                                            <ul className="absolute z-50 w-full bg-white dark:bg-gray-800 border dark:border-gray-600 shadow-lg rounded-md mt-1 max-h-60 overflow-y-auto">
                                                {isSearchingProducts ? (
                                                    <li className="p-2 text-gray-500 dark:text-gray-400">Carregando...</li>
                                                ) : productSearchResults.filter(p => !itemsInCartIds.has(p.id)).length > 0 ? (
                                                    productSearchResults.filter(p => !itemsInCartIds.has(p.id)).map(p => (
                                                        <li
                                                            key={p.id}
                                                            className="p-3 hover:bg-primary-50 dark:hover:bg-primary-700/20 cursor-pointer text-gray-800 dark:text-gray-200 border-b dark:border-gray-700 last:border-0"
                                                            onMouseDown={() => handleSelectProduct(p)}
                                                        >
                                                            <div className="flex justify-between items-center">
                                                                <span>{p.name}</span>
                                                                <span className="text-xs text-gray-500">Estoque: {p.stock_quantity}</span>
                                                            </div>
                                                            <div className="text-sm mt-1">
                                                                {p.is_on_sale && p.promotional_price ? (
                                                                    <>
                                                                        <span className="font-bold text-red-500 mr-2">{formatCurrency(p.promotional_price)}</span>
                                                                        {p.sale_price && p.sale_price > p.promotional_price &&
                                                                            <span className="text-gray-500 line-through text-xs">{formatCurrency(p.sale_price)}</span>
                                                                        }
                                                                    </>
                                                                ) : (
                                                                    <span className="font-bold">{formatCurrency(p.sale_price)}</span>
                                                                )}
                                                            </div>
                                                        </li>
                                                    ))
                                                ) : (
                                                    <li className="p-2 text-gray-500 dark:text-gray-400">Nenhum produto encontrado.</li>
                                                )}
                                            </ul>
                                        )}
                                    </div>
                                    <div className="flex gap-2 w-full sm:w-auto">
                                        <div className="w-24 sm:w-20">
                                            <label className="block font-medium dark:text-gray-300 mb-1 text-sm">Qtd.</label>
                                            <input type="number" value={currentItem.quantity} onChange={e => setCurrentItem(p => ({ ...p, quantity: parseInt(e.target.value) || 1 }))} min="1" className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100" />
                                        </div>
                                        <button type="button" onClick={handleAddItem} disabled={!currentItem.product} className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 flex-1 sm:flex-none disabled:bg-gray-400 h-[42px] self-end">Adicionar</button>
                                    </div>
                                </div>
                                {errors.items && <p className="text-red-500 text-xs mt-2">{errors.items}</p>}
                                <ul className="space-y-3 mt-4">
                                    {newSale.items.map(item => (
                                        <li key={item.productId} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg gap-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="font-semibold text-gray-800 dark:text-gray-200 truncate">{item.name}</p>
                                            </div>
                                            <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto">
                                                <div className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                                                    <span>{item.quantity} x </span>
                                                    {item.originalUnitPrice && item.originalUnitPrice > item.unitPrice ? (
                                                        <>
                                                            <span className="font-bold text-red-500">{formatCurrency(item.unitPrice)}</span>
                                                            <s className="ml-2 text-xs">{formatCurrency(item.originalUnitPrice)}</s>
                                                        </>
                                                    ) : (
                                                        <span>{formatCurrency(item.unitPrice)}</span>
                                                    )}
                                                </div>
                                                <span className="font-bold text-lg text-gray-800 dark:text-gray-100 min-w-[80px] text-right">{formatCurrency(item.unitPrice * item.quantity)}</span>
                                                <button type="button" onClick={() => handleRemoveItem(item.productId)} className="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-100 dark:hover:bg-red-900/50">
                                                    <span className="material-symbols-outlined">delete</span>
                                                </button>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block font-medium dark:text-gray-300 mb-1">Forma de Pagamento</label>
                                    <select value={newSale.paymentMethod} onChange={e => setNewSale(p => ({ ...p, paymentMethod: e.target.value as PaymentMethod }))} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                                        <option value="cash">À vista (Dinheiro/Cartão)</option>
                                        <option value="pix">PIX</option>
                                        <option value="credit">Crediário</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block font-medium dark:text-gray-300 mb-1">Desconto (R$)</label>
                                    <input
                                        type="text"
                                        inputMode="decimal"
                                        placeholder="0,00"
                                        value={newSale.discountAmount}
                                        onChange={e => {
                                            const value = e.target.value;
                                            if (/^(\d+([,.]\d{0,2})?)?$/.test(value)) {
                                                setNewSale(p => ({ ...p, discountAmount: value }));
                                            }
                                        }}
                                        className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 ${errors.discountAmount ? 'border-red-500' : ''}`}
                                    />
                                    {errors.discountAmount && <p className="text-red-500 text-xs mt-1">{errors.discountAmount}</p>}
                                </div>
                            </div>

                            {newSale.paymentMethod === 'credit' && (
                                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
                                    <div>
                                        <label className="block font-medium dark:text-gray-300 mb-1">Nº de Parcelas</label>
                                        <select
                                            value={newSale.numInstallments}
                                            onChange={e => setNewSale(p => ({ ...p, numInstallments: e.target.value }))}
                                            className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                                        >
                                            {[...Array(12)].map((_, i) => (
                                                <option key={i + 1} value={i + 1}>{i + 1}x</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block font-medium dark:text-gray-300 mb-1">1ª Parcela para</label>
                                        <input
                                            type="date"
                                            value={newSale.firstDueDate ? newSale.firstDueDate.toISOString().split('T')[0] : ''}
                                            onChange={e => setNewSale(p => ({ ...p, firstDueDate: e.target.value ? new Date(e.target.value) : new Date() }))}
                                            className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                                            style={{ colorScheme: 'dark' }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-4 mt-4 border-t dark:border-gray-700">
                            <div className="text-xl font-bold text-gray-800 dark:text-gray-100">
                                Total: <span className="text-green-600 dark:text-green-400">{formatCurrency(totalNewSale - numericDiscount)}</span>
                            </div>
                            <button type="submit" disabled={isSubmitting} className="w-full sm:w-auto bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:bg-green-700 transition-transform hover:scale-105 disabled:opacity-70 disabled:scale-100 flex justify-center items-center">
                                {isSubmitting ? (
                                    <>
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                                        Processando...
                                    </>
                                ) : (
                                    'Finalizar Venda'
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div className="w-full md:w-auto flex-1">
                    <div className="relative w-full md:w-80">
                        <input
                            type="text"
                            placeholder="Buscar por cliente..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            className="w-full p-3 pr-10 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                        />
                        {searchTerm && (
                            <button
                                type="button"
                                onClick={() => setSearchTerm('')}
                                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                aria-label="Limpar busca"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-4 w-full md:w-auto">
                    <select
                        name="status"
                        value={filters.status}
                        onChange={handleFilterChange}
                        className="p-3 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 flex-1 md:flex-none"
                    >
                        <option value="">Todos Status</option>
                        <option value="completed">Finalizada</option>
                        <option value="canceled">Cancelada</option>
                    </select>
                    <button
                        onClick={() => navigate('/sales/new')}
                        className="flex items-center justify-center bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors whitespace-nowrap"
                    >
                        <span className="material-symbols-outlined mr-2">add_shopping_cart</span>
                        Nova Venda
                    </button>
                </div>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalSales}</span> venda(s) encontrada(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {isLoading && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Carregando vendas...</p>}
                {!isLoading && salesWithDetails.length === 0 && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Nenhuma venda encontrada.</p>}
                {!isLoading && salesWithDetails.map(sale => (
                    <div
                        key={sale.id}
                        onClick={() => navigate(`/sales/${sale.id}`)}
                        className={`bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 ${sale.status === 'canceled' ? 'opacity-60' : ''}`}
                    >
                        <div className="flex justify-between items-start gap-2">
                            <div className="min-w-0 flex-1">
                                <p className="font-bold text-lg text-gray-800 dark:text-gray-100 truncate">{sale.customerName}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">{!isNaN(sale.date.getTime()) ? sale.date.toLocaleDateString('pt-BR') : 'Data inválida'}</p>
                            </div>
                            <div className="text-right flex-shrink-0">
                                <p className={`font-bold text-lg ${sale.status === 'canceled' ? 'text-red-500 line-through' : 'text-green-600 dark:text-green-400'}`}>
                                    {formatCurrency(sale.total)}
                                </p>
                                <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold mt-1 ${sale.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                    {sale.status === 'completed' ? 'Finalizada' : 'Cancelada'}
                                </span>
                            </div>
                        </div>
                        <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                            <div className={`flex items-center text-sm font-medium ${paymentMethodInfo[sale.paymentMethod].color}`}>
                                <span className="material-symbols-outlined text-lg mr-1">{paymentMethodInfo[sale.paymentMethod].icon}</span>
                                {paymentMethodInfo[sale.paymentMethod].text}
                            </div>
                            <button className="text-primary-600 dark:text-primary-400 text-sm font-bold flex items-center">
                                Detalhes <span className="material-symbols-outlined text-base ml-1">chevron_right</span>
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Desktop View */}
            <div className="hidden md:block bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Data</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Cliente</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Pagamento</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Total</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr><td colSpan={6} className="text-center py-10 text-gray-500 dark:text-gray-400">Carregando vendas...</td></tr>
                            ) : salesWithDetails.length === 0 ? (
                                <tr><td colSpan={6} className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhuma venda encontrada.</td></tr>
                            ) : (
                                salesWithDetails.map(sale => (
                                    <tr
                                        key={sale.id}
                                        className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${sale.status === 'canceled' ? 'opacity-60' : ''}`}
                                        onClick={() => navigate(`/sales/${sale.id}`)}
                                    >
                                        <td className="py-3 px-4 text-gray-500 dark:text-gray-400">
                                            {!isNaN(sale.date.getTime()) ? sale.date.toLocaleDateString('pt-BR') : 'Data inválida'}
                                        </td>
                                        <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{sale.customerName}</td>
                                        <td className="py-3 px-4 text-center">
                                            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 ${paymentMethodInfo[sale.paymentMethod].color}`}>
                                                <span className="material-symbols-outlined text-sm mr-1">{paymentMethodInfo[sale.paymentMethod].icon}</span>
                                                {paymentMethodInfo[sale.paymentMethod].text}
                                            </div>
                                        </td>
                                        <td className={`py-3 px-4 text-right font-semibold ${sale.status === 'canceled' ? 'text-gray-400 line-through' : 'text-green-600 dark:text-green-400'}`}>
                                            {formatCurrency(sale.total)}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${sale.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                                {sale.status === 'completed' ? 'Finalizada' : 'Cancelada'}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); navigate(`/sales/${sale.id}`); }}
                                                className="text-blue-600 hover:text-blue-800 p-2 rounded-full hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                                                title="Ver Detalhes"
                                            >
                                                <span className="material-symbols-outlined">visibility</span>
                                            </button>
                                        </td>
                                    </tr>
                                )))}
                        </tbody>
                    </table>
                </div>
            </div>

            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
        </div>
    );
};

export default Sales;
