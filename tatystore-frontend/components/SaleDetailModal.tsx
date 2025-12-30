
import React from 'react';
import Modal from './Modal';
import { Sale, Customer, Product } from '../types';
import InstallmentStatusBadge from './InstallmentStatusBadge';

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

interface SaleDetailModalProps {
    isOpen: boolean;
    onClose: () => void;
    sale: Sale | null;
    customer: Customer | null;
    products: Product[];
    title?: string;
}

const SaleDetailModal: React.FC<SaleDetailModalProps> = ({ isOpen, onClose, sale, customer, products, title = "Detalhes da Venda" }) => {
    if (!isOpen || !sale || !customer) return null;

    const handleWhatsAppShare = () => {
        const phone = customer.phone.replace(/\D/g, '');
        let message = `Olá, ${customer.name}!\n\n`;
        message += `Obrigado pela sua compra realizada em ${new Date(sale.date).toLocaleDateString('pt-BR')}.\n\n`;
        message += '*Resumo da Compra:*\n';
        sale.items.forEach(item => {
            const product = products.find(p => p.id === item.productId);
            message += `- ${item.quantity}x ${product?.name || 'Produto desconhecido'}\n`;
        });
        message += `\n*Total: ${formatCurrency(sale.total)}*\n\n`;

        if (sale.paymentMethod === 'credit' && sale.installments.length > 0) {
            message += '*Detalhes do Parcelamento:*\n';
            sale.installments.forEach((inst, index) => {
                // Use remaining amount logic here
                const remaining = inst.remainingAmount !== undefined ? inst.remainingAmount : inst.amount;
                const isPaid = inst.status === 'paid';
                const isPartial = remaining > 0 && remaining < inst.amount;
                
                let statusText = '';
                if (isPaid) statusText = ' (Pago)';
                else if (isPartial) statusText = ` (Restam: ${formatCurrency(remaining)})`;

                message += `Parcela ${index + 1}/${sale.installments.length}: ${formatCurrency(inst.amount)}${statusText} (Vencimento: ${new Date(inst.dueDate).toLocaleDateString('pt-BR')})\n`;
            });
            message += '\nAgradecemos a preferência!';
        } else {
            message += 'Agradecemos a preferência!';
        }

        const whatsappUrl = `https://wa.me/55${phone}?text=${encodeURIComponent(message)}`;
        window.open(whatsappUrl, '_blank');
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title}>
            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                <div>
                    <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100">{customer.name}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{customer.phone}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Data da Compra: {new Date(sale.date).toLocaleDateString('pt-BR')}</p>
                </div>
                <div className="border-t dark:border-gray-700 pt-4">
                    <h4 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">Itens</h4>
                    <ul className="divide-y dark:divide-gray-700">
                        {sale.items.map(item => {
                             const product = products.find(p => p.id === item.productId);
                             return (
                                <li key={item.productId} className="flex justify-between py-2">
                                    <div>
                                        <p className="font-medium text-gray-800 dark:text-gray-200">{product?.name || 'Produto'}</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">{item.quantity} x {formatCurrency(item.unitPrice)}</p>
                                    </div>
                                    <p className="font-semibold text-gray-800 dark:text-gray-200">{formatCurrency(item.quantity * item.unitPrice)}</p>
                                </li>
                             )
                        })}
                    </ul>
                     <div className="flex justify-end font-bold text-xl mt-2 py-2 border-t dark:border-gray-700 text-gray-800 dark:text-gray-100">
                        <span>Total:</span>
                        <span className="ml-2">{formatCurrency(sale.total)}</span>
                    </div>
                </div>

                {sale.paymentMethod === 'credit' && sale.installments.length > 0 && (
                    <div className="border-t dark:border-gray-700 pt-4">
                        <h4 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">Parcelamento</h4>
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-100 dark:bg-gray-700">
                                <tr>
                                    <th className="p-2 font-semibold text-gray-600 dark:text-gray-300">Vencimento</th>
                                    <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-right">Valor</th>
                                    <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-right">Restante</th>
                                    <th className="p-2 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sale.installments.map(inst => {
                                    const remaining = inst.remainingAmount !== undefined ? inst.remainingAmount : inst.amount;
                                    return (
                                        <tr key={inst.id} className="border-t dark:border-gray-700">
                                            <td className="p-2 text-gray-800 dark:text-gray-200">{new Date(inst.dueDate).toLocaleDateString('pt-BR')}</td>
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
             <div className="flex justify-end mt-6 pt-4 border-t dark:border-gray-700">
                <button 
                    onClick={handleWhatsAppShare}
                    className="flex items-center bg-green-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:bg-green-600 transition-colors"
                >
                    <span className="material-symbols-outlined mr-2">share</span>
                    Enviar via WhatsApp
                </button>
            </div>
        </Modal>
    );
};

export default SaleDetailModal;
