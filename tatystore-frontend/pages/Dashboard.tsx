
import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import DashboardCard from '../components/DashboardCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from 'recharts';
import { Product, Customer } from '../types';
import { logger } from '../utils/logger';
import { handleApiError } from '../utils/errorHandler';
import { safeParseDate } from '../utils/dateUtils';

interface DashboardContext {
    chartThemeColor: string;
    addToast: (msg: string, type?: 'success' | 'error') => void;
    apiUrl: string;
}

interface LowStockProduct {
    id: string;
    name: string;
    brand: string;
    stock_quantity: number;
    min_stock: number;
}

// safeParseDate agora importado de utils/dateUtils.ts

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

type ChartPeriod = 'today' | 'week' | 'month' | 'last30';

const Spinner: React.FC = () => (
    <div className="flex justify-center items-center h-full py-10">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    </div>
);

const Dashboard: React.FC = () => {
    const { chartThemeColor, addToast, apiUrl } = useOutletContext<DashboardContext>();
    const navigate = useNavigate();
    const { tokens, user } = useAuth();

    const [chartPeriod, setChartPeriod] = useState<ChartPeriod>('week');
    const [isLoading, setIsLoading] = useState(true);

    const [dashboardStats, setDashboardStats] = useState<any>(null);
    const [lowStockProducts, setLowStockProducts] = useState<LowStockProduct[]>([]);
    const [overdueCustomers, setOverdueCustomers] = useState<Customer[]>([]);
    const [salesOverTimeData, setSalesOverTimeData] = useState<any[]>([]);

    const isSalesperson = useMemo(() => user?.role?.toLowerCase() === 'vendedor', [user]);

    const fetchDashboardData = useCallback(async () => {
        if (!tokens) return;
        setIsLoading(true);

        const periodParam = chartPeriod === 'last30' ? 'month' : chartPeriod;

        const summaryPromise = fetch(`${apiUrl}/reports/sales-summary?period=${periodParam}`, {
            headers: { 'Authorization': `Bearer ${tokens.access_token}` }
        });
        const overdueInstallmentsPromise = fetch(`${apiUrl}/installments/overdue?limit=5000`, {
            headers: { 'Authorization': `Bearer ${tokens.access_token}` }
        });
        const allCustomersPromise = fetch(`${apiUrl}/customers/?limit=5000&show_inactive=true`, {
            headers: { 'Authorization': `Bearer ${tokens.access_token}` }
        });
        const productsPromise = fetch(`${apiUrl}/products/?limit=2000&show_inactive=false`, {
            headers: { 'Authorization': `Bearer ${tokens.access_token}` }
        });

        try {
            const responses = await Promise.all([
                summaryPromise,
                overdueInstallmentsPromise,
                allCustomersPromise,
                productsPromise
            ]);

            const data = await Promise.all(responses.map(res => {
                if (!res.ok) {
                    logger.error(`Failed to fetch ${res.url}`, { status: res.statusText }, 'Dashboard');
                    return null;
                }
                if (res.status === 204) return null;
                return res.json();
            }));

            const summaryData = data[0];
            const overdueInstallmentsResult = data[1];
            const allCustomersResult = data[2];
            const allProductsData = data[3];

            setDashboardStats(summaryData);

            // Client-side logic to determine overdue customers
            const overdueInstallments = overdueInstallmentsResult?.data || overdueInstallmentsResult?.items;
            const allCustomers = allCustomersResult?.data || allCustomersResult?.items;

            if (overdueInstallments && allCustomers) {
                // Get unique customer IDs from the list of overdue installments
                const overdueCustomerIds = new Set(overdueInstallments.map((inst: any) => String(inst.customer_id)));

                // Filter the full customer list to get details of only those with overdue installments
                const overdueCustomersDetails = allCustomers.filter((cust: any) => overdueCustomerIds.has(String(cust.id)));

                setOverdueCustomers(overdueCustomersDetails);
            } else {
                setOverdueCustomers([]);
            }

            // Client-side logic for low stock products
            const productsList = allProductsData?.data || allProductsData?.items || [];
            if (Array.isArray(productsList)) {
                const lowStock = productsList.filter((p: Product) => p.stock_quantity <= p.min_stock);
                setLowStockProducts(lowStock);
            } else {
                setLowStockProducts([]);
            }

            // Chart data processing
            if (summaryData && Array.isArray(summaryData.sales) && summaryData.sales.length > 0) {
                const profitMargin = (summaryData.profit > 0 && summaryData.total_revenue > 0)
                    ? summaryData.profit / summaryData.total_revenue
                    : 0;

                const dailyData = summaryData.sales.reduce((acc: any, sale: any) => {
                    const saleDate = safeParseDate(sale.sale_date);
                    if (isNaN(saleDate.getTime())) {
                        return acc;
                    }

                    const dayKey = saleDate.toISOString().split('T')[0];

                    if (!acc[dayKey]) {
                        acc[dayKey] = {
                            date: saleDate.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
                            revenue: 0,
                            profit: 0,
                        };
                    }

                    const revenue = parseFloat(sale.total_amount || 0);
                    acc[dayKey].revenue += revenue;
                    acc[dayKey].profit += revenue * profitMargin;

                    return acc;
                }, {} as { [key: string]: { date: string, revenue: number, profit: number } });

                const chartData = Object.keys(dailyData)
                    .sort()
                    .map(key => dailyData[key]);

                setSalesOverTimeData(chartData);
            } else {
                setSalesOverTimeData([]);
            }

        } catch (error) {
            const errorMessage = handleApiError(error, 'Dashboard - fetchDashboardData');
            addToast('Falha ao carregar dados do dashboard.', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [tokens, chartPeriod, addToast, apiUrl]);


    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    const salesCardTitle = useMemo(() => {
        switch (chartPeriod) {
            case 'today': return 'Vendas de Hoje';
            case 'week': return 'Vendas da Semana';
            case 'month': return 'Vendas do Mês';
            case 'last30': return 'Vendas (30 dias)';
            default: return 'Vendas';
        }
    }, [chartPeriod]);

    const profitCardTitle = useMemo(() => {
        switch (chartPeriod) {
            case 'today': return 'Lucro de Hoje';
            case 'week': return 'Lucro da Semana';
            case 'month': return 'Lucro do Mês';
            case 'last30': return 'Lucro (30 dias)';
            default: return 'Lucro';
        }
    }, [chartPeriod]);

    return (
        <div className="space-y-6 animate-fade-in pb-4">

            {/* Top Bar with Title and Filters */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Visão Geral</h2>

                <div className="w-full md:w-auto overflow-x-auto pb-2 md:pb-0 -mx-4 px-4 md:mx-0 md:px-0">
                    <div className="flex items-center gap-1 p-1 bg-gray-200 dark:bg-gray-700 rounded-lg w-max md:w-auto">
                        {(['today', 'week', 'month', 'last30'] as ChartPeriod[]).map(period => (
                            <button
                                key={period}
                                onClick={() => setChartPeriod(period)}
                                className={`px-4 py-2 rounded-md font-semibold transition-all text-sm whitespace-nowrap ${chartPeriod === period
                                    ? 'bg-white dark:bg-gray-600 text-primary-600 dark:text-primary-300 shadow-sm ring-1 ring-black/5'
                                    : 'bg-transparent text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-300'
                                    }`}
                            >
                                {period === 'today' ? 'Hoje' : period === 'week' ? 'Esta Semana' : period === 'month' ? 'Este Mês' : 'Últimos 30 dias'}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className={`grid grid-cols-1 md:grid-cols-2 ${isSalesperson ? 'lg:grid-cols-3' : 'lg:grid-cols-4'} gap-6`}>
                <DashboardCard
                    icon="attach_money"
                    title={salesCardTitle}
                    value={formatCurrency(dashboardStats?.total_revenue)}
                    color="green"
                    tooltipText="Receita Bruta: O valor total de todas as suas vendas no período selecionado, sem descontos."
                />
                {!isSalesperson && (
                    <>
                        <DashboardCard
                            icon="trending_up"
                            title={profitCardTitle}
                            value={formatCurrency(dashboardStats?.profit)}
                            color="purple"
                            tooltipText="Lucro Bruto Estimado: A receita do período menos o custo dos produtos vendidos e os descontos aplicados."
                        />
                        <DashboardCard
                            icon="point_of_sale"
                            title="Vendas no Período"
                            value={dashboardStats?.total_sales || 0}
                            color="blue"
                            tooltipText="Número total de vendas individuais realizadas."
                        >
                            <p className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                                Ticket Médio: <span className="font-bold text-gray-700 dark:text-gray-200">{formatCurrency(dashboardStats?.average_ticket)}</span>
                            </p>
                        </DashboardCard>
                    </>
                )}
                {isSalesperson && (
                    <DashboardCard
                        icon="point_of_sale"
                        title="Vendas no Período"
                        value={dashboardStats?.total_sales || 0}
                        color="blue"
                        tooltipText="Número total de vendas individuais realizadas no período selecionado."
                    />
                )}
                <DashboardCard
                    icon="pending_actions"
                    title="Cobranças Atrasadas"
                    value={overdueCustomers.length}
                    color="red"
                    tooltipText="Número total de clientes com uma ou mais parcelas de crediário vencidas."
                />
            </div>

            {/* Gráfico */}
            <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md border border-gray-100 dark:border-gray-700/50 flex flex-col">
                <div className="mb-6">
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary-600">bar_chart</span>
                        Evolução de Vendas
                    </h2>
                </div>
                <div className="flex-grow h-64 sm:h-80">
                    {isLoading ? (
                        <Spinner />
                    ) : !salesOverTimeData || salesOverTimeData.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Nenhum dado para exibir neste período.</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={salesOverTimeData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(128, 128, 128, 0.3)" />
                                <XAxis dataKey="date" tick={{ fill: 'rgb(156 163 175)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                <YAxis tickFormatter={(value) => formatCurrency(value as number)} tick={{ fill: 'rgb(156 163 175)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    formatter={(value) => formatCurrency(value as number)}
                                    contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.95)', borderColor: 'rgba(55, 65, 81, 1)', borderRadius: '0.5rem', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                                    labelStyle={{ color: '#F3F4F6', fontWeight: 'bold', marginBottom: '0.5rem' }}
                                    itemStyle={{ padding: 0 }}
                                    cursor={{ fill: 'rgba(107, 114, 128, 0.1)' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                                <Bar dataKey="revenue" name="Receita" fill={chartThemeColor} radius={[4, 4, 0, 0]} />
                                {!isSalesperson && <Bar dataKey="profit" name="Lucro" fill="#10B981" radius={[4, 4, 0, 0]} />}
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            {/* Cards Inferiores */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md border border-gray-100 dark:border-gray-700/50">
                    <h2 className="text-xl font-bold mb-4 flex items-center text-gray-800 dark:text-gray-100">
                        <span className="material-symbols-outlined text-red-500 mr-2 bg-red-100 dark:bg-red-900/30 p-1.5 rounded-lg">notifications_active</span>
                        Clientes em Atraso ({overdueCustomers.length})
                    </h2>
                    {isLoading ? <Spinner /> : overdueCustomers.length > 0 ? (
                        <>
                            <ul className="divide-y divide-gray-100 dark:divide-gray-700 max-h-64 overflow-y-auto pr-2">
                                {overdueCustomers.slice(0, 5).map(customer => (
                                    <li key={customer.id} className="py-3">
                                        <button onClick={() => navigate(`/customers/${customer.id}`)} className="w-full text-left flex justify-between items-center group transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 p-2 rounded-lg -mx-2">
                                            <div>
                                                <p className="font-bold text-gray-800 dark:text-gray-200 group-hover:text-primary-600 dark:group-hover:text-primary-300">{customer.name}</p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                                    Total Devido: <span className="font-semibold text-red-500">{formatCurrency(customer.total_debt)}</span>
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Contato</p>
                                                <p className="font-mono text-sm text-gray-700 dark:text-gray-300">{customer.phone}</p>
                                            </div>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-4 text-right pt-2 border-t border-gray-100 dark:border-gray-700">
                                <button onClick={() => navigate('/reports?type=overdue')} className="text-sm font-semibold text-primary-600 dark:text-primary-300 hover:underline flex items-center justify-end gap-1 ml-auto">
                                    Ver relatório completo
                                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                            <span className="material-symbols-outlined text-5xl text-green-200 dark:text-green-900/50 mb-2">check_circle</span>
                            <p className="text-gray-500 dark:text-gray-400 font-medium">Nenhuma cobrança atrasada.</p>
                            <p className="text-xs text-gray-400">Parabéns pela gestão!</p>
                        </div>
                    )}
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md border border-gray-100 dark:border-gray-700/50">
                    <h2 className="text-xl font-bold mb-4 flex items-center text-gray-800 dark:text-gray-100">
                        <span className="material-symbols-outlined text-orange-500 mr-2 bg-orange-100 dark:bg-orange-900/30 p-1.5 rounded-lg">inventory_2</span>
                        Estoque Baixo ({lowStockProducts.length})
                    </h2>
                    {isLoading ? <Spinner /> : lowStockProducts.length > 0 ? (
                        <>
                            <ul className="divide-y divide-gray-100 dark:divide-gray-700 max-h-64 overflow-y-auto pr-2">
                                {lowStockProducts.slice(0, 5).map(product => (
                                    <li key={product.id} className="py-3">
                                        <button onClick={() => navigate(`/products/${product.id}`)} className="w-full text-left flex justify-between items-center group transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 p-2 rounded-lg -mx-2">
                                            <div>
                                                <p className="font-bold text-gray-800 dark:text-gray-200 group-hover:text-primary-600 dark:group-hover:text-primary-300">{product.name}</p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400">{product.brand}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Restam</p>
                                                <span className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium ${product.stock_quantity === 0 ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'}`}>
                                                    {product.stock_quantity} un
                                                </span>
                                            </div>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-4 text-right pt-2 border-t border-gray-100 dark:border-gray-700">
                                <button onClick={() => navigate('/reports?type=low_stock')} className="text-sm font-semibold text-primary-600 dark:text-primary-300 hover:underline flex items-center justify-end gap-1 ml-auto">
                                    Ver relatório completo
                                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                            <span className="material-symbols-outlined text-5xl text-blue-200 dark:text-blue-900/50 mb-2">inventory</span>
                            <p className="text-gray-500 dark:text-gray-400 font-medium">Estoque abastecido.</p>
                            <p className="text-xs text-gray-400">Nenhum produto abaixo do mínimo.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
