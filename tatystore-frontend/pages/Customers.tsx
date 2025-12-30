
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useOutletContext, useParams, useNavigate, useLocation } from 'react-router-dom';
import { Customer, Sale, Installment, Product, InstallmentStatus, SaleItem, PaymentMethod, User } from '../types';
import InstallmentStatusBadge from '../components/InstallmentStatusBadge';
import { useAuth } from '../App';
import Pagination from '../components/Pagination';
import { maskCPF, maskPhone, validateEmail, unmask } from '../utils/formatters';
import InstallmentPaymentControl from '../components/InstallmentPaymentControl';
import { safeParseDate } from '../utils/dateUtils';


interface CustomersContext {
    customers: Customer[];
    totalCustomers: number;
    fetchCustomers: (filters: any) => Promise<void>;
    addToast: (message: string, type?: 'success' | 'error') => void;
    apiUrl: string;
    user: User | null;
}

type CustomerView = 'list' | 'details' | 'form' | 'confirmToggle' | 'payment';

// safeParseDate agora importado de utils/dateUtils.ts

const formatCurrency = (value: number) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);


const Customers: React.FC = () => {
    const { customers, totalCustomers, fetchCustomers, addToast, apiUrl, user } = useOutletContext<CustomersContext>();
    const { customerId } = useParams<{ customerId: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { tokens } = useAuth();

    const [view, setView] = useState<CustomerView>('list');
    const [isEditing, setIsEditing] = useState(false);
    const [showInactive, setShowInactive] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [errors, setErrors] = useState<{ [key: string]: string }>({});

    type CustomerFormData = Omit<Customer, 'id' | 'status' | 'is_active' | 'total_debt' | 'company_id' | 'created_at' | 'updated_at'>;
    const initialCustomerState: CustomerFormData = { name: '', phone: '', address: '', cpf: '', email: '' };
    const [customerForm, setCustomerForm] = useState<CustomerFormData>(initialCustomerState);

    const [customerToToggle, setCustomerToToggle] = useState<Customer | null>(null);
    const [installmentToPay, setInstallmentToPay] = useState<Installment | null>(null);
    const [listIsLoading, setListIsLoading] = useState(true);

    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil(totalCustomers / ITEMS_PER_PAGE), [totalCustomers]);

    // States for details view
    const [detailedCustomer, setDetailedCustomer] = useState<Customer | null>(null);
    const [customerInstallments, setCustomerInstallments] = useState<Installment[]>([]);
    const [customerSales, setCustomerSales] = useState<Sale[]>([]);
    const [customerStats, setCustomerStats] = useState<any | null>(null);
    const [customerTopProducts, setCustomerTopProducts] = useState<any[]>([]);
    const [isDetailsLoading, setIsDetailsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'open' | 'history'>('open');

    const isManager = useMemo(() => user?.role?.toLowerCase().includes('gerente'), [user]);

    const openInstallments = useMemo(() => {
        return customerInstallments
            .filter(inst => inst.status === 'pending' || inst.status === 'overdue')
            .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
    }, [customerInstallments]);

    const doFetchCustomers = useCallback(async () => {
        setListIsLoading(true);
        await fetchCustomers({ page: currentPage, searchTerm, showInactive });
        setListIsLoading(false);
    }, [fetchCustomers, currentPage, searchTerm, showInactive]);

    const fetchCustomerDetails = useCallback(async (id: string) => {
        if (!tokens) return;
        setIsDetailsLoading(true);
        setDetailedCustomer(null);
        setCustomerInstallments([]);
        setCustomerSales([]);
        setCustomerStats(null);
        setCustomerTopProducts([]);

        try {
            const customerRes = await fetch(`${apiUrl}/customers/${id}`, { headers: { 'Authorization': `Bearer ${tokens.access_token}` } });
            if (!customerRes.ok) {
                addToast('Cliente não encontrado.', 'error');
                navigate('/customers', { replace: true });
                return;
            }
            const customerData = await customerRes.json();
            setDetailedCustomer({
                ...customerData,
                id: String(customerData.id),
                status: customerData.is_active ? 'active' : 'inactive',
                total_debt: customerData.total_debt || 0,
            });

            const [salesByCustomerResult, topProductsResult, installmentsResult] = await Promise.allSettled([
                fetch(`${apiUrl}/sales/by-customer/${id}`, { headers: { 'Authorization': `Bearer ${tokens.access_token}` } }),
                fetch(`${apiUrl}/sales/products/top-sellers?customer_id=${id}`, { headers: { 'Authorization': `Bearer ${tokens.access_token}` } }),
                fetch(`${apiUrl}/installments/?customer_id=${id}&limit=1000`, { headers: { 'Authorization': `Bearer ${tokens.access_token}` } })
            ]);

            if (salesByCustomerResult.status === 'fulfilled' && salesByCustomerResult.value.ok) {
                const salesByCustomerData = await salesByCustomerResult.value.json();
                const stats = salesByCustomerData.statistics;
                if (stats) {
                    const lastPurchase = safeParseDate(stats.last_purchase_date);
                    setCustomerStats({
                        totalPurchases: stats.total_sales || 0,
                        totalSpent: stats.total_spent || 0,
                        lastPurchaseDate: !isNaN(lastPurchase.getTime()) ? lastPurchase.toLocaleDateString('pt-BR') : 'Nenhuma'
                    });
                }

                const salesList = salesByCustomerData.sales || salesByCustomerData.items || [];
                if (Array.isArray(salesList)) {
                    const parsedSales: Sale[] = salesList.map((s: any) => ({
                        id: String(s.id),
                        customerId: String(s.customer_id),
                        items: [],
                        total: s.total_amount,
                        totalCost: 0,
                        discountAmount: s.discount_amount || 0,
                        paymentMethod: (s.payment_type || 'cash').toLowerCase() as PaymentMethod,
                        installments: [],
                        date: safeParseDate(s.created_at || s.sale_date),
                        status: (s.status || 'completed').toLowerCase() as 'completed' | 'canceled',
                    }));
                    setCustomerSales(parsedSales.sort((a, b) => b.date.getTime() - a.date.getTime()));
                }
            }

            if (topProductsResult.status === 'fulfilled' && topProductsResult.value.ok) {
                const topProductsData = await topProductsResult.value.json();
                const topProducts = Array.isArray(topProductsData) ? topProductsData : (topProductsData?.products || topProductsData?.items || []);
                setCustomerTopProducts(topProducts);
            }

            if (installmentsResult.status === 'fulfilled' && installmentsResult.value.ok) {
                const installmentsData = await installmentsResult.value.json();
                const installmentsList = Array.isArray(installmentsData) ? installmentsData : (installmentsData.data || installmentsData.items || []);
                const parsedInstallments: Installment[] = installmentsList.map((inst: any) => ({
                    id: String(inst.id),
                    saleId: String(inst.sale_id),
                    customerId: String(inst.customer_id),
                    amount: inst.amount,
                    dueDate: safeParseDate(inst.due_date),
                    status: (inst.status || 'pending').toLowerCase() as InstallmentStatus,
                    saleDate: safeParseDate(inst.sale?.sale_date || inst.created_at),
                    // We inject customer name here since we know it from the parent
                    customerName: customerData.name,
                    remainingAmount: inst.remaining_amount
                })).sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime());
                setCustomerInstallments(parsedInstallments);
            } else {
                addToast('Não foi possível carregar as parcelas do cliente.', 'error');
            }

        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido ao carregar cliente.', 'error');
            navigate('/customers', { replace: true });
        } finally {
            setIsDetailsLoading(false);
        }
    }, [tokens, addToast, navigate, apiUrl]);


    useEffect(() => {
        if (view === 'list') {
            const debouncedFetch = setTimeout(() => {
                doFetchCustomers();
            }, 300);
            return () => clearTimeout(debouncedFetch);
        }
    }, [view, doFetchCustomers]);

    useEffect(() => {
        if (view === 'details' && customerId) {
            fetchCustomerDetails(customerId);
        }
    }, [view, customerId, fetchCustomerDetails]);

    // Reset state when visiting root path
    useEffect(() => {
        if (location.pathname === '/customers') {
            setSearchTerm('');
            setShowInactive(false);
            setCurrentPage(1);
            setView('list');
        }
    }, [location.pathname]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, showInactive]);

    useEffect(() => {
        if (customerId) {
            if (customerId === 'new') {
                setView('form');
                setIsEditing(false);
                setDetailedCustomer(null);
            } else {
                setView('details');
            }
        } else {
            setView('list');
        }
    }, [customerId]);

    const validateCustomerForm = () => {
        const newErrors: { [key: string]: string } = {};
        if (!customerForm.name.trim()) newErrors.name = "Nome é obrigatório.";
        if (!customerForm.address.trim()) newErrors.address = "Endereço é obrigatório.";
        if (!customerForm.email.trim()) {
            newErrors.email = "Email é obrigatório.";
        } else if (!validateEmail(customerForm.email)) {
            newErrors.email = "Formato de email inválido.";
        }

        const cleanedCpf = unmask(customerForm.cpf || '');
        if (cleanedCpf.length !== 11) newErrors.cpf = "CPF deve conter 11 dígitos.";

        const cleanedPhone = unmask(customerForm.phone || '');
        if (cleanedPhone.length < 10 || cleanedPhone.length > 11) newErrors.phone = "Telefone deve conter 10 ou 11 dígitos.";

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    useEffect(() => {
        if (view === 'form' && isEditing && detailedCustomer) {
            const { name, phone, address, cpf, email } = detailedCustomer;
            setCustomerForm({ name, phone, address, cpf, email });
        } else {
            setCustomerForm(initialCustomerState);
        }
    }, [view, isEditing, detailedCustomer])

    const handleFormSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateCustomerForm() || !tokens) return;

        const method = isEditing ? 'PUT' : 'POST';
        const url = isEditing ? `${apiUrl}/customers/${customerId}` : `${apiUrl}/customers/`;

        const body: any = {
            ...customerForm,
            cpf: unmask(customerForm.cpf),
            phone: unmask(customerForm.phone),
        };

        if (isEditing && detailedCustomer) {
            body.is_active = detailedCustomer.is_active;
        }

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: JSON.stringify(body)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Falha ao ${isEditing ? 'atualizar' : 'salvar'} cliente.`);
            }
            addToast(`Cliente ${isEditing ? 'atualizado' : 'salvo'} com sucesso!`);

            if (isEditing) {
                await fetchCustomers({ page: currentPage, searchTerm, showInactive });
                navigate(`/customers/${customerId}`);
            } else {
                const newCustomer = await response.json();
                await fetchCustomers({ page: 1 });
                navigate(`/customers/${newCustomer.id}`);
            }
            setCustomerForm(initialCustomerState);
            setIsEditing(false);
            setErrors({});
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido', 'error');
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let { name, value } = e.target;
        if (name === 'cpf') {
            value = maskCPF(value);
        }
        if (name === 'phone') {
            value = maskPhone(value);
        }
        setCustomerForm(prev => ({ ...prev, [name]: value }));
    };

    const handleToggleStatus = useCallback(async () => {
        if (!customerToToggle || !tokens) return;

        const isActivating = !customerToToggle.is_active;
        const method = isActivating ? 'PUT' : 'DELETE';
        const url = `${apiUrl}/customers/${customerToToggle.id}`;

        try {
            let response;
            if (method === 'DELETE') {
                response = await fetch(url, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${tokens.access_token}` }
                });
            } else { // PUT for activating
                const body = {
                    name: customerToToggle.name,
                    email: customerToToggle.email,
                    phone: unmask(customerToToggle.phone),
                    cpf: unmask(customerToToggle.cpf),
                    address: customerToToggle.address,
                    is_active: true
                };
                response = await fetch(url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${tokens.access_token}`
                    },
                    body: JSON.stringify(body)
                });
            }

            if (!response.ok && response.status !== 204) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Falha ao atualizar status do cliente.');
            }

            addToast('Status do cliente atualizado com sucesso!');
            await doFetchCustomers(); // Refresh list in background

            const wasOnDetailsPage = customerId === String(customerToToggle.id);
            if (wasOnDetailsPage) {
                if (isActivating) {
                    await fetchCustomerDetails(customerToToggle.id);
                    setView('details'); // Stay on details
                } else {
                    navigate('/customers', { replace: true }); // Navigate away
                }
            } else {
                setView('list'); // Action was from list, stay on list
            }
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido', 'error');
            setView('list'); // On error, revert to list view for safety
        } finally {
            setCustomerToToggle(null);
        }
    }, [customerToToggle, tokens, apiUrl, addToast, doFetchCustomers, customerId, fetchCustomerDetails, navigate]);

    const handleOpenPayConfirm = (installment: Installment) => {
        setInstallmentToPay(installment);
        setView('payment');
    };

    const handlePaymentSuccess = async () => {
        if (customerId) {
            await fetchCustomerDetails(customerId); // Re-fetch details after payment
        }
    };

    const handlePageChange = (page: number) => {
        if (page > 0 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    if (view === 'payment' && installmentToPay) {
        return (
            <InstallmentPaymentControl
                installmentId={installmentToPay.id}
                customerName={detailedCustomer?.name}
                onBack={() => {
                    setInstallmentToPay(null);
                    setView('details');
                }}
                onPaymentSuccess={handlePaymentSuccess}
                apiUrl={apiUrl}
                addToast={addToast}
            />
        );
    }

    if (view === 'confirmToggle' && customerToToggle) {
        const actionText = customerToToggle.status === 'active' ? 'desativar' : 'reativar';
        const confirmButtonColor = customerToToggle.status === 'active' ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';

        return (
            <div>
                <BackButton onClick={() => navigate('/customers')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar {actionText.charAt(0).toUpperCase() + actionText.slice(1)}</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">Tem certeza que deseja {actionText} o cliente "{customerToToggle.name}"?</p>
                    <div className="flex justify-center gap-4">
                        <button onClick={() => setView('list')} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors">Cancelar</button>
                        <button onClick={handleToggleStatus} className={`text-white font-bold py-2 px-6 rounded-lg transition-colors ${confirmButtonColor}`}>{actionText.charAt(0).toUpperCase() + actionText.slice(1)}</button>
                    </div>
                </div>
            </div>
        );
    }

    if (view === 'form') {
        return (
            <div>
                <BackButton onClick={() => navigate(customerId === 'new' ? '/customers' : `/customers/${customerId}`)} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">{isEditing ? "Editar Cliente" : "Adicionar Novo Cliente"}</h1>
                    <form onSubmit={handleFormSubmit} noValidate>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome Completo</label>
                                <input type="text" name="name" placeholder="Ex: Maria da Silva" value={customerForm.name} onChange={handleInputChange} required className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`} />
                                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                                <input type="email" name="email" placeholder="Ex: maria@email.com" value={customerForm.email} onChange={handleInputChange} required className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`} />
                                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CPF</label>
                                <input type="text" name="cpf" placeholder="Ex: 123.456.789-00" value={customerForm.cpf} onChange={handleInputChange} required className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.cpf ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`} />
                                {errors.cpf && <p className="text-red-500 text-xs mt-1">{errors.cpf}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                                <input type="tel" name="phone" placeholder="Ex: (11) 98765-4321" value={customerForm.phone} onChange={handleInputChange} required className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.phone ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`} />
                                {errors.phone && <p className="text-red-500 text-xs mt-1">{errors.phone}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço Completo</label>
                                <input type="text" name="address" placeholder="Ex: Rua das Flores, 123, Bairro, Cidade, UF" value={customerForm.address} onChange={handleInputChange} required className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.address ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`} />
                                {errors.address && <p className="text-red-500 text-xs mt-1">{errors.address}</p>}
                            </div>
                        </div>
                        <div className="flex justify-end mt-6 pt-4 border-t dark:border-gray-700">
                            <button type="submit" className="bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors">Salvar Cliente</button>
                        </div>
                    </form>
                </div>
            </div>
        );
    }

    if (view === 'details') {
        if (isDetailsLoading || !detailedCustomer) {
            return <div className="text-center py-10 text-gray-500 dark:text-gray-400">Carregando detalhes do cliente...</div>;
        }

        const { totalSpent, lastPurchaseDate } = customerStats || { totalPurchases: 0, totalSpent: 0, lastPurchaseDate: 'Nenhuma' };

        const handleSendDebtReminder = () => {
            if (!detailedCustomer) return;

            const phone = unmask(detailedCustomer.phone);

            const overdueInstallments = customerInstallments.filter((inst: Installment) => inst.status === 'overdue');

            if (overdueInstallments.length === 0) {
                addToast(`${detailedCustomer.name} não possui parcelas vencidas.`, 'success');
                return;
            }

            const totalOverdueAmount = overdueInstallments.reduce((sum, inst) => {
                // Usa o valor restante se disponível, senão o valor original
                const valueToPay = inst.remainingAmount !== undefined ? Number(inst.remainingAmount) : Number(inst.amount);
                return sum + valueToPay;
            }, 0);

            let message = `Olá, ${detailedCustomer.name}! Tudo bem?\n\n`;
            message += `Verificamos que há algumas parcelas em aberto conosco. O valor total do seu débito referente às parcelas vencidas é de *${formatCurrency(totalOverdueAmount)}*.\n\n`;
            message += `*Detalhes das Parcelas Vencidas:*\n`;
            overdueInstallments.forEach((inst: Installment) => {
                const dueDate = inst.dueDate;
                const formattedDate = !isNaN(dueDate.getTime()) ? dueDate.toLocaleDateString('pt-BR') : 'Data inválida';
                // Usa o valor restante na mensagem também
                const valueToPay = inst.remainingAmount !== undefined ? Number(inst.remainingAmount) : Number(inst.amount);
                message += `- Parcela de ${formatCurrency(valueToPay)} com vencimento em ${formattedDate}.\n`;
            });
            message += `\nPor favor, entre em contato para regularizar sua situação.\n\nAgradecemos a sua atenção!`;

            const whatsappUrl = `https://wa.me/55${phone}?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        };

        const nextDueDate = customerInstallments
            .filter(i => i.status === 'pending' || i.status === 'overdue')
            .sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime())[0]?.dueDate;

        return (
            <div>
                <BackButton onClick={() => navigate('/customers')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <div>
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-2xl font-bold mb-1 text-gray-800 dark:text-gray-100">{detailedCustomer.name}</h2>
                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${detailedCustomer.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                    {detailedCustomer.status === 'active' ? 'Ativo' : 'Inativo'}
                                </span>
                            </div>
                            <div className="flex gap-2">
                                {detailedCustomer.total_debt > 0 && (
                                    <button onClick={handleSendDebtReminder} className="flex items-center gap-2 text-white bg-green-500 hover:bg-green-600 px-3 py-1.5 rounded-lg transition-colors text-sm font-semibold" title={`Cobrar Dívida Atrasada (${formatCurrency(detailedCustomer.total_debt)})`}>
                                        <span className="material-symbols-outlined text-base">sms</span>
                                        Cobrar via WhatsApp
                                    </button>
                                )}
                                <button onClick={() => { setIsEditing(true); setView('form'); setErrors({}); }} className="text-blue-600 hover:text-blue-800 p-2 rounded-full bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900/80 transition-colors" title="Editar Cliente">
                                    <span className="material-symbols-outlined">edit</span>
                                </button>
                                <button onClick={() => { setCustomerToToggle(detailedCustomer); setView('confirmToggle'); }} className={`${detailedCustomer.status === 'active' ? 'text-red-600 hover:text-red-800 bg-red-50 hover:bg-red-100 dark:bg-red-900/50 dark:text-red-300 dark:hover:bg-red-900/80' : 'text-green-600 hover:text-green-800 bg-green-50 hover:bg-green-100 dark:bg-green-900/50 dark:text-green-300 dark:hover:bg-green-900/80'} p-2 rounded-full transition-colors`} title={detailedCustomer.status === 'active' ? 'Desativar Cliente' : 'Reativar Cliente'}>
                                    <span className="material-symbols-outlined">{detailedCustomer.status === 'active' ? 'toggle_off' : 'toggle_on'}</span>
                                </button>
                            </div>
                        </div>
                        <div className="text-gray-500 dark:text-gray-400 my-4 space-y-1">
                            <p className="flex items-center"><span className="material-symbols-outlined text-sm align-middle mr-1">email</span>{detailedCustomer.email}</p>
                            <p className="flex items-center"><span className="material-symbols-outlined text-sm align-middle mr-1">call</span>{maskPhone(detailedCustomer.phone)}</p>
                            <p className="flex items-center"><span className="material-symbols-outlined text-sm align-middle mr-1">badge</span>{maskCPF(detailedCustomer.cpf)}</p>
                            <p className="flex items-center"><span className="material-symbols-outlined text-sm align-middle mr-1">home</span>{detailedCustomer.address}</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 my-6">
                    <div className="bg-red-50 dark:bg-red-900/30 p-4 rounded-lg text-center">
                        <h4 className="text-sm font-semibold text-red-800 dark:text-red-200">Dívida Total</h4>
                        <p className="text-2xl font-bold text-red-600 dark:text-red-400">{formatCurrency(detailedCustomer.total_debt)}</p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg text-center">
                        <h4 className="text-sm font-semibold text-green-800 dark:text-green-200">Total Gasto na Loja</h4>
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">{formatCurrency(totalSpent)}</p>
                    </div>
                    <div className="bg-yellow-50 dark:bg-yellow-900/30 p-4 rounded-lg text-center">
                        <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200">Próximo Vencimento</h4>
                        <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{nextDueDate && !isNaN(nextDueDate.getTime()) ? nextDueDate.toLocaleDateString('pt-BR') : 'N/A'}</p>
                    </div>
                    <div className="bg-gray-100 dark:bg-gray-700/50 p-4 rounded-lg text-center">
                        <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Última Compra</h4>
                        <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">{lastPurchaseDate}</p>
                    </div>
                </div>

                <div className="mt-6">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                        <div className="border-b border-gray-200 dark:border-gray-700">
                            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                                <button
                                    onClick={() => setActiveTab('open')}
                                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'open' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:border-gray-600'}`}
                                >
                                    Parcelas em Aberto ({openInstallments.length})
                                </button>
                                <button
                                    onClick={() => setActiveTab('history')}
                                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'history' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:border-gray-600'}`}
                                >
                                    Histórico de Compras ({customerSales.length})
                                </button>
                            </nav>
                        </div>

                        <div className="mt-6">
                            {activeTab === 'open' && (
                                <div className="overflow-x-auto">
                                    {openInstallments.length > 0 ? (
                                        <table className="w-full text-left">
                                            <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                                                <tr>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300">Venda</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300">Vencimento</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-right">Valor</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-right">Restante</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                                    {isManager && <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {openInstallments.map((inst) => (
                                                    <tr key={inst.id} className="border-b border-gray-100 dark:border-gray-700">
                                                        <td className="py-3 px-3">
                                                            <button onClick={() => navigate(`/sales/${inst.saleId}`)} className="text-primary-600 dark:text-primary-400 hover:underline text-sm font-mono">
                                                                #{inst.saleId.substring(0, 8)}...
                                                            </button>
                                                            <div className="text-xs text-gray-500">{inst.saleDate && !isNaN(inst.saleDate.getTime()) ? inst.saleDate.toLocaleDateString('pt-BR') : 'N/A'}</div>
                                                        </td>
                                                        <td className="py-3 px-3 text-gray-800 dark:text-gray-200">{!isNaN(inst.dueDate.getTime()) ? inst.dueDate.toLocaleDateString('pt-BR') : 'Inválida'}</td>
                                                        <td className="py-3 px-3 text-right font-semibold text-gray-800 dark:text-gray-200">{formatCurrency(inst.amount)}</td>
                                                        <td className="py-3 px-3 text-right font-bold text-red-600 dark:text-red-400">{formatCurrency(inst.remainingAmount !== undefined ? inst.remainingAmount : inst.amount)}</td>
                                                        <td className="py-3 px-3 text-center"><InstallmentStatusBadge status={inst.status} /></td>
                                                        {isManager && (
                                                            <td className="py-3 px-3 text-center">
                                                                <button onClick={() => handleOpenPayConfirm(inst)} className="bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300 font-bold py-1 px-3 rounded-lg text-sm hover:bg-green-200 dark:hover:bg-green-900">Pagar</button>
                                                            </td>
                                                        )}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    ) : (
                                        <p className="text-center py-6 text-gray-500 dark:text-gray-400">Nenhuma parcela em aberto. 🎉</p>
                                    )}
                                </div>
                            )}
                            {activeTab === 'history' && (
                                <div className="overflow-x-auto">
                                    {customerSales.length > 0 ? (
                                        <table className="w-full text-left">
                                            <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                                                <tr>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300">Data</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300">Pagamento</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-right">Total</th>
                                                    <th className="py-2 px-3 font-semibold text-gray-600 dark:text-gray-300 text-center"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {customerSales.map((sale) => (
                                                    <tr key={sale.id} className="border-b border-gray-100 dark:border-gray-700">
                                                        <td className="py-3 px-3 text-gray-800 dark:text-gray-200">{!isNaN(sale.date.getTime()) ? sale.date.toLocaleDateString('pt-BR') : 'Inválida'}</td>
                                                        <td className="py-3 px-3 text-gray-800 dark:text-gray-200 capitalize">{sale.paymentMethod === 'credit' ? 'Crediário' : sale.paymentMethod}</td>
                                                        <td className="py-3 px-3 text-center">
                                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${sale.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                                                {sale.status === 'completed' ? 'Finalizada' : 'Cancelada'}
                                                            </span>
                                                        </td>
                                                        <td className="py-3 px-3 text-right font-semibold text-gray-800 dark:text-gray-200">{formatCurrency(sale.total)}</td>
                                                        <td className="py-3 px-3 text-center">
                                                            <button onClick={() => navigate(`/sales/${sale.id}`)} className="text-primary-600 dark:text-primary-400 font-bold py-1 px-3 rounded-lg text-sm hover:underline">Ver Detalhes</button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    ) : (
                                        <p className="text-center py-6 text-gray-500 dark:text-gray-400">Nenhuma compra registrada.</p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
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
                            placeholder="Buscar por nome ou CPF..."
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
                <div className="w-full md:w-auto flex flex-col md:flex-row items-stretch md:items-center gap-4">
                    <label className="flex items-center cursor-pointer whitespace-nowrap p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                        <input type="checkbox" checked={showInactive} onChange={() => setShowInactive(!showInactive)} className="mr-2 h-4 w-4 rounded text-primary-600 focus:ring-primary-500" />
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Mostrar inativos</span>
                    </label>
                    <button
                        onClick={() => { setIsEditing(false); navigate('/customers/new'); }}
                        className="flex items-center justify-center bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors"
                    >
                        <span className="material-symbols-outlined mr-2">person_add</span>
                        Novo Cliente
                    </button>
                </div>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalCustomers}</span> cliente(s) encontrado(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {listIsLoading && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Carregando clientes...</p>}
                {!listIsLoading && customers.length === 0 && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Nenhum cliente encontrado.</p>}
                {!listIsLoading && customers.map(customer => {
                    const debt = customer.total_debt || 0;
                    return (
                        <div
                            key={customer.id}
                            onClick={() => navigate(`/customers/${customer.id}`)}
                            className={`p-4 rounded-2xl shadow-md border ${customer.status === 'inactive' ? 'opacity-60' : ''} ${debt > 0 ? 'bg-red-50/50 dark:bg-red-900/20 border-red-200 dark:border-red-800' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'}`}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{customer.name}</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">{maskPhone(customer.phone)}</p>
                                </div>
                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${customer.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                    {customer.status === 'active' ? 'Ativo' : 'Inativo'}
                                </span>
                            </div>
                            <div className="text-right mt-2">
                                <p className={`font-semibold ${debt > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                                    {formatCurrency(debt)}
                                </p>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Desktop View */}
            <div className="hidden md:block bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Cliente</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Contato</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">CPF</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Dívida Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {listIsLoading ? (
                                <tr><td colSpan={5} className="text-center py-10 text-gray-500 dark:text-gray-400">Carregando clientes...</td></tr>
                            ) : customers.length === 0 ? (
                                <tr><td colSpan={5} className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhum cliente encontrado.</td></tr>
                            ) : (
                                customers.map(customer => {
                                    const debt = customer.total_debt || 0;
                                    const debtColorClass = debt === 0
                                        ? 'text-green-500 dark:text-green-400'
                                        : 'text-red-500 dark:text-red-400';
                                    return (
                                        <tr
                                            key={customer.id}
                                            className={`border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${customer.status === 'inactive' ? 'opacity-60' : ''}`}
                                            onClick={() => navigate(`/customers/${customer.id}`)}
                                        >
                                            <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{customer.name}</td>
                                            <td className="py-3 px-4 text-gray-500 dark:text-gray-400">
                                                <div>{maskPhone(customer.phone)}</div>
                                                <div className="text-xs">{customer.email}</div>
                                            </td>
                                            <td className="py-3 px-4 text-gray-500 dark:text-gray-400">{maskCPF(customer.cpf)}</td>
                                            <td className="py-3 px-4 text-center">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${customer.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                                    {customer.status === 'active' ? 'Ativo' : 'Inativo'}
                                                </span>
                                            </td>
                                            <td className={`py-3 px-4 font-semibold text-right ${debtColorClass}`}>
                                                {formatCurrency(debt)}
                                            </td>
                                        </tr>
                                    )
                                }))}
                        </tbody>
                    </table>
                </div>
            </div>

            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
        </div>
    );
};

export default Customers;
