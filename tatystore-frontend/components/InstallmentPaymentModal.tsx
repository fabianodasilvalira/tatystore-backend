import React, { useState, useEffect, useCallback } from 'react';
import Modal from './Modal';
import { Installment, InstallmentDetail } from '../types';
import { useAuth } from '../App';
import InstallmentStatusBadge from './InstallmentStatusBadge';

interface InstallmentPaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    installment: Installment | null;
    apiUrl: string;
    onPaymentSuccess: () => void;
    addToast: (message: string, type?: 'success' | 'error') => void;
}

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const InstallmentPaymentModal: React.FC<InstallmentPaymentModalProps> = ({
    isOpen,
    onClose,
    installment,
    apiUrl,
    onPaymentSuccess,
    addToast
}) => {
    const { tokens } = useAuth();
    const [detail, setDetail] = useState<InstallmentDetail | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [paymentAmount, setPaymentAmount] = useState<string>('');
    const [error, setError] = useState<string>('');

    // Fetch details when modal opens
    useEffect(() => {
        if (isOpen && installment && tokens) {
            fetchDetails();
            setPaymentAmount('');
            setError('');
        } else {
            setDetail(null);
        }
    }, [isOpen, installment, tokens]);

    const fetchDetails = async () => {
        if (!installment || !tokens) return;
        setIsLoading(true);
        try {
            const response = await fetch(`${apiUrl}/installment-payments/installments/${installment.id}/detail`, {
                headers: { 'Authorization': `Bearer ${tokens.access_token}` }
            });
            if (!response.ok) throw new Error('Falha ao carregar detalhes da parcela.');
            const data = await response.json();
            setDetail(data);
            // CORRECTION: Use toFixed(2) instead of toString() to prevent long floats
            const remaining = typeof data.remaining_amount === 'string' ? parseFloat(data.remaining_amount) : data.remaining_amount;
            setPaymentAmount(remaining.toFixed(2));
        } catch (err) {
            addToast('Erro ao carregar detalhes.', 'error');
            onClose();
        } finally {
            setIsLoading(false);
        }
    };

    const handlePayment = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!detail || !tokens) return;

        const amount = parseFloat(paymentAmount.replace(',', '.'));
        
        if (isNaN(amount) || amount <= 0) {
            setError('Digite um valor válido maior que zero.');
            return;
        }

        if (amount > detail.remaining_amount + 0.01) { // Small epsilon for floating point
            setError(`O valor não pode exceder o restante de ${formatCurrency(detail.remaining_amount)}.`);
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
                    amount: amount
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Falha ao registrar pagamento.');
            }

            addToast('Pagamento registrado com sucesso!', 'success');
            onPaymentSuccess();
            
            // If fully paid, close, otherwise refresh details
            if (amount >= detail.remaining_amount - 0.01) {
                onClose();
            } else {
                fetchDetails();
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao processar pagamento.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Pagamento de Parcela">
            {isLoading || !detail ? (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
                    Carregando detalhes...
                </div>
            ) : (
                <div className="space-y-6">
                    {/* Header Info */}
                    <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Cliente</span>
                            <span className="font-bold text-gray-800 dark:text-gray-200">{installment?.customerName}</span>
                        </div>
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Vencimento</span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">
                                {new Date(detail.due_date).toLocaleDateString('pt-BR')}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Status</span>
                            <InstallmentStatusBadge status={detail.status} />
                        </div>
                    </div>

                    {/* Progress Bar & Stats */}
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600 dark:text-gray-300">Pago: {formatCurrency(detail.total_paid)}</span>
                            <span className="text-gray-600 dark:text-gray-300">Total: {formatCurrency(detail.amount)}</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
                            <div 
                                className="bg-green-600 h-2.5 rounded-full transition-all duration-500" 
                                style={{ width: `${Math.min((detail.total_paid / detail.amount) * 100, 100)}%` }}
                            ></div>
                        </div>
                        <div className="text-right mt-1">
                            <span className="text-sm font-semibold text-red-600 dark:text-red-400">
                                Restante: {formatCurrency(detail.remaining_amount)}
                            </span>
                        </div>
                    </div>

                    {/* Payment Form */}
                    {detail.status !== 'paid' && detail.remaining_amount > 0 && (
                        <form onSubmit={handlePayment} className="border-t dark:border-gray-700 pt-4">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Valor do Pagamento
                            </label>
                            <div className="flex gap-2">
                                <div className="relative flex-1">
                                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400">R$</span>
                                    <input 
                                        type="number" 
                                        step="0.01"
                                        max={detail.remaining_amount}
                                        value={paymentAmount}
                                        onChange={(e) => {
                                            setPaymentAmount(e.target.value);
                                            setError('');
                                        }}
                                        className="w-full pl-10 p-2 border rounded-lg bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500"
                                        placeholder="0,00"
                                    />
                                </div>
                                <button 
                                    type="submit" 
                                    disabled={isSubmitting || !paymentAmount}
                                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-bold transition-colors flex items-center gap-2"
                                >
                                    {isSubmitting ? 'Processando...' : 'Pagar'}
                                    {!isSubmitting && <span className="material-symbols-outlined text-sm">payments</span>}
                                </button>
                            </div>
                            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                        </form>
                    )}

                    {/* History List */}
                    {detail.payments.length > 0 && (
                        <div className="border-t dark:border-gray-700 pt-4">
                            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Histórico de Pagamentos</h4>
                            <div className="max-h-40 overflow-y-auto space-y-2 pr-1">
                                {detail.payments.map((pay) => (
                                    <div key={pay.id} className="flex justify-between items-center text-sm p-2 bg-gray-50 dark:bg-gray-700/30 rounded">
                                        <span className="text-gray-600 dark:text-gray-400">
                                            {new Date(pay.paid_at).toLocaleDateString('pt-BR')} às {new Date(pay.paid_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}
                                        </span>
                                        <span className="font-bold text-green-600 dark:text-green-400">
                                            {formatCurrency(pay.amount_paid)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </Modal>
    );
};

export default InstallmentPaymentModal;