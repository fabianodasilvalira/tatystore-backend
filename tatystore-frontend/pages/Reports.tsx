import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useOutletContext, useNavigate, useSearchParams } from 'react-router-dom';
import { Product, ReportType } from '../types';
import { useAuth } from '../App';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } from 'recharts';
import { safeParseDate } from '../utils/dateUtils';

// safeParseDate agora importado de utils/dateUtils.ts

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

interface ReportContext {
    chartThemeColor: string;
    addToast: (msg: string, type?: 'success' | 'error') => void;
    apiUrl: string;
}

type FilterType = 'today' | 'week' | 'month' | 'custom';

const ReportCard: React.FC<{ title: string; value: string | number; icon: string; tooltip?: string; colorClass?: string; }> = ({ title, value, icon, tooltip, colorClass = 'text-primary-600 dark:text-primary-300' }) => (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
        <div className="flex items-center justify-center gap-2">
            <h3 className="text-lg font-semibold text-gray-500 dark:text-gray-400">{title}</h3>
            {tooltip && (
                <div className="relative group">
                    <span className="material-symbols-outlined text-gray-400 cursor-help text-base">info</span>
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 text-sm font-normal text-left text-white bg-gray-900 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-10 dark:bg-gray-700">
                        {tooltip}
                        <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-gray-900 dark:border-t-gray-700"></div>
                    </div>
                </div>
            )}
        </div>
        <p className={`text-4xl font-bold mt-2 ${colorClass}`}>{value}</p>
    </div>
);

// Mobile Card Components
const MobileReportCard: React.FC<{ children: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
    <div onClick={onClick} className={`bg-white dark:bg-gray-800 p-4 rounded-xl shadow-md border dark:border-gray-700 ${onClick ? 'cursor-pointer active:scale-95 transition-transform' : ''}`}>
        {children}
    </div>
);

const MobileCardRow: React.FC<{ label: string; value: string | number; icon: string; valueColor?: string }> = ({ label, value, icon, valueColor = 'text-gray-800 dark:text-gray-100' }) => (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <span className="material-symbols-outlined text-base">{icon}</span>
            <span className="text-sm">{label}</span>
        </div>
        <span className={`font-semibold text-sm ${valueColor}`}>{value}</span>
    </div>
);

const Reports: React.FC = () => {
    const { chartThemeColor, addToast, apiUrl } = useOutletContext<ReportContext>();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const { tokens } = useAuth();

    const [reportType, setReportType] = useState<ReportType>(searchParams.get('type') as ReportType || 'sales');
    const [filterType, setFilterType] = useState<FilterType>('week');
    const [customDate, setCustomDate] = useState<string>(new Date().toISOString().split('T')[0]);

    const [metric, setMetric] = useState<'revenue' | 'quantity'>('revenue');
    const [limit, setLimit] = useState<number>(10);

    const [reportData, setReportData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const typeFromUrl = searchParams.get('type') as ReportType;
        if (typeFromUrl && typeFromUrl !== reportType) {
            setReportType(typeFromUrl);
        }
    }, [searchParams, reportType]);

    const handleSetReportType = (type: ReportType) => {
        setReportType(type);
        setSearchParams({ type });
    };

    const fetchReport = useCallback(async () => {
        if (!tokens) return;
        setIsLoading(true);
        setReportData(null);

        let endpointPath;
        let params = new URLSearchParams();

        if (reportType === 'canceled_sales') {
            const summaryParams = new URLSearchParams();
            if (filterType) summaryParams.append('period', filterType);
            if (filterType === 'custom' && customDate) {
                summaryParams.append('custom_date', customDate);
            }

            const salesParams = new URLSearchParams();
            salesParams.append('status', 'canceled');
            if (filterType === 'custom') {
                salesParams.append('period', 'custom');
                salesParams.append('start_date', customDate);
                salesParams.append('end_date', customDate);
            } else if (filterType) {
                salesParams.append('period', filterType);
            }

            try {
                const [summaryResponse, salesResponse] = await Promise.all([
                    fetch(`${apiUrl}/reports/canceled-sales?${summaryParams.toString()}`, {
                        headers: { 'Authorization': `Bearer ${tokens.access_token}` }
                    }),
                    fetch(`${apiUrl}/sales/?${salesParams.toString()}`, {
                        headers: { 'Authorization': `Bearer ${tokens.access_token}` }
                    })
                ]);

                if (!summaryResponse.ok) throw new Error('Falha ao carregar resumo de vendas canceladas.');
                if (!salesResponse.ok) throw new Error('Falha ao carregar lista de vendas canceladas.');

                const summaryData = await summaryResponse.json();
                const salesResult = await salesResponse.json();

                const salesList = (salesResult.data || []).map((s: any) => ({
                    sale_id: s.id,
                    customer_name: s.customer?.name || 'Cliente',
                    sale_date: s.created_at || s.sale_date,
                    total_amount: s.total_amount
                }));

                setReportData({
                    ...summaryData,
                    sales: salesList
                });
            } catch (error) {
                addToast(error instanceof Error ? error.message : 'Erro ao carregar relatório.', 'error');
            } finally {
                setIsLoading(false);
            }
            return;
        }

        if (!['overdue', 'low_stock'].includes(reportType)) {
            params.append('period', filterType);
            if (filterType === 'custom' && customDate) {
                params.append('custom_date', customDate);
                params.append('start_date', customDate);
                params.append('end_date', customDate);
            }
        }

        switch (reportType) {
            case 'sales':
            case 'profit':
                endpointPath = 'reports/sales-summary';
                break;
            case 'overdue':
                endpointPath = 'reports/overdue-customers';
                break;
            case 'sold_products':
                endpointPath = 'sales/products/top-sellers';
                params.append('metric', metric);
                params.append('limit', String(limit));
                break;
            default:
                endpointPath = `reports/${reportType.replace(/_/g, '-')}`;
        }


        try {
            const response = await fetch(`${apiUrl}/${endpointPath}?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Falha ao carregar relatório de ${reportType}`);
            }
            const responseData = await response.json();
            const data = responseData.data !== undefined ? responseData.data : responseData;
            setReportData(data);
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Erro desconhecido', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [reportType, filterType, customDate, tokens, addToast, apiUrl, metric, limit]);

    useEffect(() => {
        fetchReport();
    }, [fetchReport]);

    const reportOptions: { id: ReportType, name: string, icon: string }[] = [
        { id: 'sales', name: 'Vendas', icon: 'monitoring' },
        { id: 'profit', name: 'Lucro', icon: 'show_chart' },
        { id: 'sold_products', name: 'Produtos Vendidos', icon: 'receipt_long' },
        { id: 'canceled_sales', name: 'Vendas Canceladas', icon: 'cancel' },
        { id: 'overdue', name: 'Cobranças', icon: 'pending_actions' },
        { id: 'low_stock', name: 'Estoque Baixo', icon: 'production_quantity_limits' }
    ];

    const renderMobileList = (items: any[], renderCard: (item: any) => React.ReactNode) => (
        <div className="space-y-3 md:hidden">
            {items.map(renderCard)}
        </div>
    );

    const renderDesktopTable = (columns: { header: string; key: string; render?: (item: any) => React.ReactNode; className?: string }[], data: any[], onRowClick: (item: any) => void) => (
        <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left">
                <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                    <tr>
                        {columns.map(col => <th key={col.header} className={`py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 ${col.className}`}>{col.header}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {data.map((item, index) => (
                        <tr key={index} onClick={() => onRowClick(item)} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                            {columns.map(col => (
                                <td key={col.key} className={`py-3 px-4 ${col.className}`}>
                                    {col.render ? col.render(item) : item[col.key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const renderReportContent = () => {
        if (isLoading) return <div className="text-center py-10">Carregando dados do relatório...</div>;
        if (!reportData) return <div className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhum dado encontrado para os filtros selecionados.</div>;

        switch (reportType) {
            case 'sales':
                const salesColumns = [
                    { header: 'Cliente', key: 'customer_name', render: (item: any) => <span className="font-medium text-gray-800 dark:text-gray-100">{item.customer_name}</span> },
                    {
                        header: 'Data', key: 'sale_date', render: (item: any) => {
                            const date = safeParseDate(item.sale_date);
                            return <span className="text-gray-600 dark:text-gray-400">{!isNaN(date.getTime()) ? date.toLocaleDateString('pt-BR') : 'N/A'}</span>;
                        }
                    },
                    { header: 'Valor', key: 'total_amount', className: 'text-right', render: (item: any) => <span className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(item.total_amount)}</span> }
                ];
                return (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <ReportCard title="Receita Total" value={formatCurrency(reportData.total_revenue)} icon="attach_money" colorClass="text-green-600 dark:text-green-400" />
                            <ReportCard title="Vendas Realizadas" value={reportData.total_sales} icon="receipt_long" colorClass="text-blue-600 dark:text-blue-400" />
                            <ReportCard title="Descontos Concedidos" value={formatCurrency(reportData.total_discount)} icon="local_offer" colorClass="text-yellow-600 dark:text-yellow-400" />
                            <ReportCard title="Ticket Médio" value={formatCurrency(reportData.average_ticket)} icon="trending_up" colorClass="text-purple-600 dark:text-purple-400" />
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md">
                            <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-100">Lista de Vendas</h2>
                            {reportData.sales?.length > 0 ? (
                                <>
                                    {renderMobileList(reportData.sales, (sale: any) => {
                                        const date = safeParseDate(sale.sale_date);
                                        return (
                                            <MobileReportCard key={sale.sale_id} onClick={() => navigate(`/sales/${sale.sale_id}`)}>
                                                <div className="flex justify-between items-center">
                                                    <p className="font-bold text-gray-800 dark:text-gray-100">{sale.customer_name}</p>
                                                    <p className="font-semibold text-green-600 dark:text-green-400 text-lg">{formatCurrency(sale.total_amount)}</p>
                                                </div>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">{!isNaN(date.getTime()) ? date.toLocaleDateString('pt-BR') : 'N/A'}</p>
                                            </MobileReportCard>
                                        );
                                    })}
                                    {renderDesktopTable(salesColumns, reportData.sales, (sale: any) => navigate(`/sales/${sale.sale_id}`))}
                                </>
                            ) : <p className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhuma venda encontrada no período.</p>}
                        </div>
                    </>
                );
            case 'profit':
                const profitChartData = [{ name: 'Resumo Financeiro', Receita: reportData.total_revenue, Custo: reportData.total_cost, Lucro: reportData.profit }];
                return (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <ReportCard title="Receita Bruta" value={formatCurrency(reportData.total_revenue)} icon="attach_money" colorClass="text-green-600 dark:text-green-400" />
                            <ReportCard title="Custo dos Produtos" value={formatCurrency(reportData.total_cost)} icon="shopping_cart" colorClass="text-red-600 dark:text-red-400" />
                            <ReportCard title="Lucro Bruto" value={formatCurrency(reportData.profit)} icon="show_chart" colorClass="text-purple-600 dark:text-purple-400" />
                            <ReportCard title="Margem de Lucro" value={`${(reportData.margin_percentage || 0).toFixed(1)}%`} icon="percent" colorClass="text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md h-96">
                            <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">Análise Financeira do Período</h2>
                            <ResponsiveContainer width="100%" height="90%">
                                <BarChart data={profitChartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(128, 128, 128, 0.3)" />
                                    <XAxis type="number" tickFormatter={(value) => formatCurrency(value as number)} tick={{ fill: 'rgb(156 163 175)' }} />
                                    <YAxis type="category" dataKey="name" tick={{ fill: 'rgb(156 163 175)' }} width={150} />
                                    <Tooltip formatter={(value) => formatCurrency(value as number)} contentStyle={{ backgroundColor: 'rgba(31, 41, 55, 0.8)', borderColor: 'rgba(55, 65, 81, 1)', borderRadius: '0.5rem' }} labelStyle={{ color: '#E5E7EB' }} />
                                    <Legend wrapperStyle={{ color: '#9CA3AF' }} />
                                    <Bar dataKey="Receita" fill={chartThemeColor} />
                                    <Bar dataKey="Custo" fill="#EF4444" />
                                    <Bar dataKey="Lucro" fill="#16A34A" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </>
                );
            case 'sold_products':
                const soldProductsData = Array.isArray(reportData) ? reportData : (reportData?.products || []);
                const soldProductsColumns = [
                    { header: 'Produto', key: 'name', render: (item: any) => <span className="font-medium text-gray-800 dark:text-gray-100">{item.name}</span> },
                    { header: 'Nº de Compras', key: 'purchase_count', className: 'text-center' },
                    { header: 'Qtd. Vendida', key: 'quantity_sold', className: 'text-center' },
                    { header: 'Receita Gerada', key: 'revenue', className: 'text-right', render: (item: any) => <span className="font-semibold text-green-600 dark:text-green-400">{formatCurrency(item.revenue)}</span> }
                ];
                return (
                    <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Produtos Mais Vendidos</h2>
                            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
                                <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
                                    <button onClick={() => setMetric('revenue')} className={`px-3 py-1.5 rounded-md font-semibold transition-colors text-sm ${metric === 'revenue' ? 'bg-white dark:bg-gray-800 text-primary-700 dark:text-primary-300 shadow-sm' : 'bg-transparent text-gray-600 dark:text-gray-300 hover:text-primary-700 dark:hover:text-primary-300'}`}>Receita</button>
                                    <button onClick={() => setMetric('quantity')} className={`px-3 py-1.5 rounded-md font-semibold transition-colors text-sm ${metric === 'quantity' ? 'bg-white dark:bg-gray-800 text-primary-700 dark:text-primary-300 shadow-sm' : 'bg-transparent text-gray-600 dark:text-gray-300 hover:text-primary-700 dark:hover:text-primary-300'}`}>Quantidade</button>
                                </div>
                                <div className="flex items-center">
                                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-2 whitespace-nowrap">Exibir Top:</label>
                                    <select value={limit} onChange={e => setLimit(Number(e.target.value))} className="p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                                        <option value={10}>10</option>
                                        <option value={20}>20</option>
                                        <option value={50}>50</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        {soldProductsData.length > 0 ? (
                            <>
                                {renderMobileList(soldProductsData, (item: any) => (
                                    <MobileReportCard key={item.product_id} onClick={() => navigate(`/products/${item.product_id}`)}>
                                        <p className="font-bold text-gray-800 dark:text-gray-100">{item.name}</p>
                                        <MobileCardRow label="Receita Gerada" value={formatCurrency(item.revenue)} icon="attach_money" valueColor="text-green-600 dark:text-green-400" />
                                        <MobileCardRow label="Qtd. Vendida" value={item.quantity_sold} icon="tag" />
                                        <MobileCardRow label="Nº de Compras" value={item.purchase_count} icon="shopping_cart" />
                                    </MobileReportCard>
                                ))}
                                {renderDesktopTable(soldProductsColumns, soldProductsData, (item: any) => navigate(`/products/${item.product_id}`))}
                            </>
                        ) : <p className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhum produto vendido no período.</p>}
                    </div>
                );
            case 'canceled_sales':
                const canceledSalesColumns = [
                    { header: 'Cliente', key: 'customer_name', render: (item: any) => <span className="font-medium text-gray-800 dark:text-gray-100">{item.customer_name}</span> },
                    {
                        header: 'Data', key: 'sale_date', render: (item: any) => {
                            const date = safeParseDate(item.sale_date);
                            return <span className="text-gray-600 dark:text-gray-400">{!isNaN(date.getTime()) ? date.toLocaleDateString('pt-BR') : 'N/A'}</span>;
                        }
                    },
                    { header: 'Valor', key: 'total_amount', className: 'text-right', render: (item: any) => <span className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(item.total_amount)}</span> }
                ];
                return (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                            <ReportCard title="Vendas Canceladas" value={reportData.canceled_count} icon="cancel" colorClass="text-red-600 dark:text-red-400" />
                            <ReportCard title="Valor Perdido" value={formatCurrency(reportData.total_amount)} icon="money_off" colorClass="text-red-600 dark:text-red-400" />
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md">
                            <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-100">Lista de Vendas Canceladas</h2>
                            {reportData.sales?.length > 0 ? (
                                <>
                                    {renderMobileList(reportData.sales, (sale: any) => {
                                        const date = safeParseDate(sale.sale_date);
                                        return (
                                            <MobileReportCard key={sale.sale_id} onClick={() => navigate(`/sales/${sale.sale_id}`)}>
                                                <div className="flex justify-between items-center">
                                                    <p className="font-bold text-gray-800 dark:text-gray-100">{sale.customer_name}</p>
                                                    <p className="font-semibold text-red-600 dark:text-red-400 text-lg">{formatCurrency(sale.total_amount)}</p>
                                                </div>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">{!isNaN(date.getTime()) ? date.toLocaleDateString('pt-BR') : 'N/A'}</p>
                                            </MobileReportCard>
                                        );
                                    })}
                                    {renderDesktopTable(canceledSalesColumns, reportData.sales, (sale: any) => navigate(`/sales/${sale.sale_id}`))}
                                </>
                            ) : <p className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhuma venda cancelada encontrada no período.</p>}
                        </div>
                    </>
                );
            case 'overdue':
                const overdueColumns = [
                    { header: 'Cliente', key: 'name', render: (item: any) => <span className="font-medium text-gray-800 dark:text-gray-100">{item.name}</span> },
                    { header: 'Contato', key: 'phone', render: (item: any) => <span className="text-gray-600 dark:text-gray-400">{item.phone}</span> },
                    { header: 'Valor Devido', key: 'total_debt', className: 'text-right', render: (item: any) => <span className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(item.total_debt)}</span> }
                ];
                const oldestDate = safeParseDate(reportData.oldest_date);
                const formattedOldestDate = !isNaN(oldestDate.getTime()) && oldestDate.getFullYear() > 1970 ? oldestDate.toLocaleDateString('pt-BR') : 'N/A';
                return (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                            <ReportCard title="Clientes com Atraso" value={reportData.overdue_count} icon="group" colorClass="text-red-600 dark:text-red-400" />
                            <ReportCard title="Valor Total Vencido" value={formatCurrency(reportData.total_amount)} icon="credit_card_off" colorClass="text-red-600 dark:text-red-400" />
                            <ReportCard title="Vencimento Mais Antigo" value={formattedOldestDate} icon="calendar_month" colorClass="text-red-600 dark:text-red-400" />
                        </div>
                        <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md">
                            <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-100">Clientes com Débitos</h2>
                            {reportData.customers?.length > 0 ? (
                                <>
                                    {renderMobileList(reportData.customers, (customer: any) => (
                                        <MobileReportCard key={customer.id} onClick={() => navigate(`/customers/${customer.id}`)}>
                                            <p className="font-bold text-gray-800 dark:text-gray-100">{customer.name}</p>
                                            <MobileCardRow label="Dívida Total" value={formatCurrency(customer.total_debt)} icon="credit_card_off" valueColor="text-red-600 dark:text-red-400" />
                                            <MobileCardRow label="Contato" value={customer.phone} icon="call" />
                                        </MobileReportCard>
                                    ))}
                                    {renderDesktopTable(overdueColumns, reportData.customers, (customer: any) => navigate(`/customers/${customer.id}`))}
                                </>
                            ) : <p className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhum cliente com débito encontrado.</p>}
                        </div>
                    </>
                );
            case 'low_stock':
                const lowStockData = Array.isArray(reportData) ? reportData : [];
                const lowStockColumns = [
                    { header: 'Produto', key: 'name', render: (item: any) => <span className="font-medium text-gray-800 dark:text-gray-100">{item.name}</span> },
                    { header: 'Estoque Atual', key: 'stock_quantity', className: 'text-center', render: (item: any) => <span className="font-bold text-red-500 dark:text-red-400">{item.stock_quantity}</span> },
                    { header: 'Estoque Mínimo', key: 'min_stock', className: 'text-center' }
                ];
                return (
                    <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-md">
                        <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-100">Produtos com Estoque Baixo</h2>
                        {lowStockData.length > 0 ? (
                            <>
                                {renderMobileList(lowStockData, (product: Product) => (
                                    <MobileReportCard key={product.id} onClick={() => navigate(`/products/${product.id}`)}>
                                        <p className="font-bold text-gray-800 dark:text-gray-100">{product.name}</p>
                                        <MobileCardRow label="Estoque Atual" value={product.stock_quantity} icon="inventory" valueColor="text-red-600 dark:text-red-400" />
                                        <MobileCardRow label="Estoque Mínimo" value={product.min_stock} icon="warning" />
                                    </MobileReportCard>
                                ))}
                                {renderDesktopTable(lowStockColumns, lowStockData, (product: Product) => navigate(`/products/${product.id}`))}
                            </>
                        ) : <p className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhum produto com estoque baixo.</p>}
                    </div>
                );
            default: return <div className="text-center py-10">Selecione um tipo de relatório.</div>;
        }
    }

    return (
        <div>
            <div className="print-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <button
                    onClick={() => window.print()}
                    className="flex items-center justify-center bg-gray-600 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-gray-700 transition-colors"
                >
                    <span className="material-symbols-outlined mr-2">print</span>
                    Imprimir
                </button>
                <div className="w-full md:w-auto">
                    <div className="hidden md:flex items-center gap-2 p-1 bg-gray-200 dark:bg-gray-700 rounded-lg">
                        {(['today', 'week', 'month'] as FilterType[]).map(p => (
                            <button
                                key={p}
                                onClick={() => setFilterType(p)}
                                className={`px-3 py-1.5 rounded-md font-semibold transition-colors text-sm ${filterType === p ? 'bg-white dark:bg-gray-800 text-primary-700 dark:text-primary-300 shadow-sm' : 'bg-transparent text-gray-600 dark:text-gray-300 hover:text-primary-700 dark:hover:text-primary-300'}`}
                            >
                                {p === 'today' ? 'Hoje' : p === 'week' ? 'Semana' : 'Mês'}
                            </button>
                        ))}
                        <input
                            type="date"
                            value={customDate}
                            onChange={(e) => {
                                setCustomDate(e.target.value);
                                setFilterType('custom');
                            }}
                            className={`px-3 py-1 rounded-md font-semibold text-sm border-2 transition-colors dark:text-gray-200 ${filterType === 'custom' ? 'bg-white dark:bg-gray-800 text-primary-700 dark:text-primary-300 border-primary-300 shadow-sm' : 'bg-transparent text-gray-600 dark:text-gray-300 border-transparent hover:border-gray-300 dark:hover:border-gray-500'}`}
                            style={{ height: '34px', outline: 'none', colorScheme: document.documentElement.classList.contains('dark') ? 'dark' : 'light' }}
                        />
                    </div>
                    <div className="md:hidden space-y-2">
                        <select
                            value={filterType}
                            onChange={e => setFilterType(e.target.value as FilterType)}
                            className="w-full p-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 shadow-sm"
                        >
                            <option value="today">Hoje</option>
                            <option value="week">Esta Semana</option>
                            <option value="month">Este Mês</option>
                            <option value="custom">Data específica...</option>
                        </select>
                        {filterType === 'custom' && (
                            <input
                                type="date"
                                value={customDate}
                                onChange={e => setCustomDate(e.target.value)}
                                className="w-full p-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 shadow-sm"
                                style={{ colorScheme: 'dark' }}
                            />
                        )}
                    </div>
                </div>
            </div>

            <div className="mb-8 print-hidden">
                <div className="flex space-x-1 sm:space-x-2 p-1 bg-gray-200 dark:bg-gray-700 rounded-xl overflow-x-auto">
                    {reportOptions.map(opt => (
                        <button
                            key={opt.id}
                            onClick={() => handleSetReportType(opt.id)}
                            className={`flex-1 flex items-center justify-center gap-2 px-3 sm:px-4 py-2 rounded-lg font-semibold transition-all duration-300 whitespace-nowrap ${reportType === opt.id
                                    ? 'bg-white dark:bg-gray-800 text-primary-600 dark:text-primary-300 shadow-sm'
                                    : 'text-gray-500 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-800 hover:text-primary-600 dark:hover:text-primary-300'
                                }`}
                        >
                            <span className="material-symbols-outlined text-xl">{opt.icon}</span>
                            <span className="text-sm">{opt.name}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="printable-content">
                {renderReportContent()}
            </div>
        </div>
    );
};

export default Reports;
