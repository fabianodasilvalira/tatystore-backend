
import React, { useState, useEffect } from 'react';
import { InstallmentDetail } from '../types';
import { useAuth } from '../App';
import InstallmentStatusBadge from './InstallmentStatusBadge';

interface InstallmentPaymentControlProps {
    installmentId: string;
    customerName?: string;
    onBack: () => void;
    onPaymentSuccess: () => void;
    apiUrl: string;
    addToast: (message: string, type?: 'success' | 'error') => void;
}

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const InstallmentPaymentControl: React.FC<InstallmentPaymentControlProps> = ({
    installmentId,
    customerName,
    onBack,
    onPaymentSuccess,
    apiUrl,
    addToast
}) => {
    const { tokens } = useAuth();
    const [detail, setDetail] = useState<InstallmentDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [paymentAmount, setPaymentAmount] = useState<string>('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');

    const fetchDetails = async () => {
        if (!tokens) return;
        setIsLoading(true);
        try {
            const response = await fetch(`${apiUrl}/installment-payments/installments/${installmentId}/detail`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Falha ao carregar detalhes.');
            const data = await response.json();
            setDetail(data);
            if (data.remaining_amount) {
                 setPaymentAmount(data.remaining_amount.toFixed(2));
            }
        } catch (err) {
            addToast('Erro ao carregar parcela.', 'error');
            onBack();
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDetails();
    }, [installmentId, tokens]);

    const handlePayment = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!detail || !tokens) return;
        
        // Handle comma or dot
        const amountVal = parseFloat(paymentAmount.replace(',', '.'));
        
        if (isNaN(amountVal) || amountVal <= 0) {
            setError('Valor inválido.');
            return;
        }
        if (amountVal > detail.remaining_amount + 0.01) {
            setError('Valor excede o restante.');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            const response = await fetch(`${apiUrl}/installment-payments/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: JSON.stringify({
                    installment_id: detail.id,
                    amount: amountVal
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Erro no pagamento.');
            }

            addToast('Pagamento realizado!', 'success');
            // onPaymentSuccess(); // Comentado para manter o usuário na página após o pagamento
            
            // Refresh para mostrar o novo saldo e histórico
            await fetchDetails();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao pagar.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) return <div className="p-8 text-center">Carregando...</div>;
    if (!detail) return <div className="p-8 text-center text-red-500">Erro ao carregar dados.</div>;

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
            <button onClick={onBack} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 mb-4">
                <span className="material-symbols-outlined">arrow_back</span>
                <span className="ml-2 font-semibold">Voltar</span>
            </button>

            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Pagamento de Parcela</h2>
            
            <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg mb-6">
                <div className="flex justify-between mb-2">
                    <span className="text-gray-500 dark:text-gray-400">Cliente</span>
                    <span className="font-bold text-gray-800 dark:text-gray-200">{customerName}</span>
                </div>
                <div className="flex justify-between mb-2">
                     <span className="text-gray-500 dark:text-gray-400">Vencimento</span>
                     <span className="font-medium text-gray-800 dark:text-gray-200">{new Date(detail.due_date).toLocaleDateString('pt-BR')}</span>
                </div>
                <div className="flex justify-between mb-2">
                     <span className="text-gray-500 dark:text-gray-400">Valor Original</span>
                     <span className="font-medium text-gray-800 dark:text-gray-200">{formatCurrency(detail.amount)}</span>
                </div>
                 <div className="flex justify-between items-center">
                    <span className="text-gray-500 dark:text-gray-400">Status</span>
                    <InstallmentStatusBadge status={detail.status} />
                </div>
            </div>

            <div className="mb-6">
                <div className="flex justify-between text-sm mb-1 text-gray-600 dark:text-gray-300">
                    <span>Pago: {formatCurrency(detail.total_paid)}</span>
                    <span>Restante: {formatCurrency(detail.remaining_amount)}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                     <div 
                        className="bg-green-500 h-3 rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min((detail.total_paid / detail.amount) * 100, 100)}%` }}
                    ></div>
                </div>
            </div>

            {detail.remaining_amount > 0 && (
                <form onSubmit={handlePayment} className="mb-8">
                     <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Valor a Pagar</label>
                     <div className="flex gap-2">
                        <input 
                            type="number" 
                            step="0.01" 
                            value={paymentAmount}
                            onChange={(e) => { setPaymentAmount(e.target.value); setError(''); }}
                            className="flex-1 p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        />
                        <button 
                            type="submit" 
                            disabled={isSubmitting}
                            className="bg-green-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-green-700 disabled:opacity-50"
                        >
                            {isSubmitting ? '...' : 'Pagar'}
                        </button>
                     </div>
                     {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                </form>
            )}

            <div>
                <h3 className="font-bold text-gray-800 dark:text-gray-100 mb-3">Histórico</h3>
                {detail.payments.length === 0 ? (
                    <p className="text-gray-500 text-sm">Nenhum pagamento registrado.</p>
                ) : (
                    <ul className="space-y-2">
                        {detail.payments.map(p => (
                            <li key={p.id} className="flex justify-between bg-gray-50 dark:bg-gray-700 p-3 rounded text-sm">
                                <span className="text-gray-600 dark:text-gray-300">
                                    {new Date(p.paid_at).toLocaleDateString('pt-BR')} {new Date(p.paid_at).toLocaleTimeString('pt-BR')}
                                </span>
                                <span className="font-bold text-green-600 dark:text-green-400">{formatCurrency(p.amount_paid)}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default InstallmentPaymentControl;
