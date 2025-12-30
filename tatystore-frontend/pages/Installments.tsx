
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useOutletContext, useNavigate, useParams, useLocation } from 'react-router-dom';
import { Installment, Customer, User, InstallmentStatus } from '../types';
import InstallmentStatusBadge from '../components/InstallmentStatusBadge';
import { useAuth } from '../App';
import Pagination from '../components/Pagination';
import InstallmentPaymentControl from '../components/InstallmentPaymentControl';

interface InstallmentsContext {
    installments: Installment[];
    totalInstallments: number;
    fetchInstallments: (filters: any) => Promise<void>;
    customers: Customer[];
    addToast: (message: string, type?: 'success' | 'error') => void;
    user: User | null;
    apiUrl: string;
}

const formatCurrency = (value: number) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const InstallmentsPage: React.FC = () => {
    const { installments, totalInstallments, fetchInstallments, customers, addToast, user, apiUrl } = useOutletContext<InstallmentsContext>();
    const navigate = useNavigate();
    const { installmentId } = useParams<{ installmentId: string }>();
    const location = useLocation();
    const { tokens } = useAuth();

    const [view, setView] = useState<'list' | 'pay'>('list');
    const [isLoading, setIsLoading] = useState(true);
    const [isUpdating, setIsUpdating] = useState(false);
    const [lastUpdateDate, setLastUpdateDate] = useState<Date | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
    const [filters, setFilters] = useState<{ customer_id: string; status_filter: InstallmentStatus | '' }>({ customer_id: '', status_filter: '' });
    
    // Estado para gerenciar qual parcela está sendo paga
    const [selectedInstallment, setSelectedInstallment] = useState<Installment | null>(null);

    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil(totalInstallments / ITEMS_PER_PAGE), [totalInstallments]);
    const isManager = useMemo(() => user?.role?.toLowerCase().includes('gerente'), [user]);

    const installmentsWithDetails = useMemo(() => {
        return installments.map(inst => {
            // Preference is given to the name coming from the API (handled in App.tsx)
            // Fallback to local customer list lookup
            let name = inst.customerName;
            if (!name || name === 'N/A') {
                 const customer = customers.find(c => c.id === inst.customerId);
                 name = customer ? customer.name : 'Cliente não encontrado';
            }
            
            return {
                ...inst,
                customerName: name,
            };
        });
    }, [installments, customers]);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedSearchTerm(searchTerm);
        }, 300);

        return () => {
            clearTimeout(handler);
        };
    }, [searchTerm]);

    // Reset state when visiting the root URL (Menu Click logic)
    useEffect(() => {
        if (location.pathname === '/installments') {
            setSearchTerm('');
            setFilters({ customer_id: '', status_filter: '' });
            setCurrentPage(1);
            // Ensure list view is active
            setView('list');
        }
    }, [location.pathname]);

    const doFetchInstallments = useCallback(async () => {
        setIsLoading(true);
        await fetchInstallments({ ...filters, page: currentPage, search: debouncedSearchTerm });
        setIsLoading(false);
    }, [fetchInstallments, filters, currentPage, debouncedSearchTerm]);

    useEffect(() => {
        if (view === 'list') {
            doFetchInstallments();
        }
    }, [doFetchInstallments, view]);

    useEffect(() => {
        setCurrentPage(1);
    }, [filters, debouncedSearchTerm]);

    useEffect(() => {
        if (installmentId) {
            // Tenta encontrar a parcela na lista atual para pegar o nome do cliente
            const foundInstallment = installmentsWithDetails.find(i => i.id === installmentId);
            if (foundInstallment) {
                setSelectedInstallment(foundInstallment);
            } else {
                // Se não estiver na lista, cria um objeto temporário com o ID
                // O componente de pagamento irá buscar os detalhes completos
                setSelectedInstallment({ id: installmentId, customerName: 'Carregando...' } as any);
            }
            setView('pay');
        } else {
            setView('list');
            setSelectedInstallment(null);
        }
    }, [installmentId, installmentsWithDetails]);

    const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value as any }));
    };

    const handleOpenPayment = (installment: Installment) => {
        navigate(`/installments/payment/${installment.id}`);
    };

    const handlePaymentSuccess = () => {
        // Recarrega a lista ao voltar, mantendo a integridade dos dados
        // O 'refresh' é garantido pois a 'view' mudará para 'list' que dispara o useEffect
        navigate('/installments');
    };

    const handleManualUpdate = async () => {
        if (!isManager) {
            addToast('Apenas gerentes podem executar esta ação.', 'error');
            return;
        }
        setIsUpdating(true);
        try {
            const response = await fetch(`${apiUrl}/cron/mark-overdue`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${tokens?.access_token}`,
                    'X-Cron-Secret': '0f2c6ddcc8b44a6fb8e4a9dfae62e0e18ebf4fe6c7d89457b58de91f0d2d54d1',
                    'Content-Type': 'application/json'
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Falha ao atualizar parcelas.');
            }

            const result = await response.json();
            const count = result.updated_count || 0;

            if (count > 0) {
                addToast(`${count} parcela(s) foram atualizadas para "Atrasada".`, 'success');
            } else {
                addToast('Nenhuma nova parcela vencida encontrada para atualizar.', 'success');
            }
            setLastUpdateDate(new Date());
            
            await doFetchInstallments();

        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Ocorreu um erro desconhecido.', 'error');
        } finally {
            setIsUpdating(false);
        }
    };

    if (view === 'pay' && selectedInstallment) {
        return (
            <InstallmentPaymentControl
                installmentId={selectedInstallment.id}
                customerName={selectedInstallment.customerName}
                onBack={() => navigate('/installments')}
                onPaymentSuccess={handlePaymentSuccess}
                apiUrl={apiUrl}
                addToast={addToast}
            />
        );
    }

    return (
        <div>
             <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-6">
                 <div className="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
                    <div className="relative w-full md:w-80">
                        <input
                            type="text"
                            placeholder="Buscar por cliente, venda..."
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
                    <select name="status_filter" value={filters.status_filter} onChange={handleFilterChange} className="w-full md:w-48 p-3 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                        <option value="">Status: Todas</option>
                        <option value="pending">Pendentes</option>
                        <option value="paid">Pagas</option>
                        <option value="overdue">Atrasadas</option>
                        <option value="canceled">Canceladas</option>
                    </select>
                 </div>
                 {isManager && (
                    <button
                        onClick={handleManualUpdate}
                        disabled={isUpdating}
                        className="flex w-full sm:w-auto items-center justify-center gap-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold py-3 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                        title="Atualizar status de parcelas vencidas"
                    >
                        <span className={`material-symbols-outlined ${isUpdating ? 'animate-spin' : ''}`}>
                            {isUpdating ? 'refresh' : 'update'}
                        </span>
                        {isUpdating ? 'Atualizando...' : 'Atualizar Vencimentos'}
                    </button>
                 )}
            </div>

            {lastUpdateDate && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 text-right">
                    Última verificação: {lastUpdateDate.toLocaleTimeString()}
                </p>
            )}

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalInstallments}</span> parcela(s) encontrada(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {isLoading && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Carregando parcelas...</p>}
                {!isLoading && installmentsWithDetails.length === 0 && <p className="text-center p-4 text-gray-500 dark:text-gray-400">Nenhuma parcela encontrada.</p>}
                {!isLoading && installmentsWithDetails.map(inst => (
                    <div 
                        key={inst.id} 
                        onClick={() => handleOpenPayment(inst)}
                        className={`p-4 rounded-2xl shadow-md border cursor-pointer flex flex-wrap gap-3 items-center justify-between ${inst.status === 'overdue' ? 'bg-red-50/50 dark:bg-red-900/20 border-red-200 dark:border-red-800' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'}`}
                    >
                        <div className="min-w-0 flex-1">
                            <p className="font-bold text-gray-800 dark:text-gray-100 truncate" title={inst.customerName}>{inst.customerName}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Venc: {new Date(inst.dueDate).toLocaleDateString('pt-BR')}</p>
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 font-mono">Ref: #{inst.saleId.substring(0, 8)}</p>
                        </div>
                        <div className="text-right flex flex-col items-end">
                            <div className="mb-1"><InstallmentStatusBadge status={inst.status} /></div>
                            <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{formatCurrency(inst.amount)}</p>
                            {inst.status !== 'paid' && (inst.remainingAmount || 0) > 0 && (
                                <p className="text-xs text-red-500 font-semibold mt-1">Restam: {formatCurrency(inst.remainingAmount!)}</p>
                            )}
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
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Cliente</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Vencimento</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Venda Ref.</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Valor</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Restante</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr><td colSpan={7} className="text-center py-10 text-gray-500 dark:text-gray-400">Carregando parcelas...</td></tr>
                            ) : installmentsWithDetails.length === 0 ? (
                                <tr><td colSpan={7} className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhuma parcela encontrada.</td></tr>
                            ) : (
                                installmentsWithDetails.map(inst => (
                                <tr 
                                    key={inst.id} 
                                    className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${inst.status === 'overdue' ? 'bg-red-50/30 dark:bg-red-900/10' : ''}`}
                                    onClick={() => handleOpenPayment(inst)}
                                >
                                    <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{inst.customerName}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400">{new Date(inst.dueDate).toLocaleDateString('pt-BR')}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400 font-mono text-xs">#{inst.saleId.substring(0, 8)}</td>
                                    <td className="py-3 px-4 font-semibold text-right text-gray-800 dark:text-gray-200">{formatCurrency(inst.amount)}</td>
                                    <td className="py-3 px-4 font-semibold text-right text-red-500 dark:text-red-400">
                                        {inst.status === 'paid' || (inst.remainingAmount || 0) === 0 ? '-' : formatCurrency(inst.remainingAmount!)}
                                    </td>
                                    <td className="py-3 px-4 text-center"><InstallmentStatusBadge status={inst.status} /></td>
                                    <td className="py-3 px-4 text-center">
                                        <button 
                                            onClick={(e) => { e.stopPropagation(); handleOpenPayment(inst); }} 
                                            className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 p-2 rounded-full transition-colors"
                                            title="Visualizar Detalhes"
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

            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
        </div>
    );
};

export default InstallmentsPage;
