import React from 'react';
import { Sale, Customer, Installment, Company } from '../types';

interface PaymentBookletProps {
    sale: Sale;
    customer: Customer;
    company: Company;
    onClose: () => void;
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const PaymentSlip: React.FC<{ sale: Sale; customer: Customer; installment: Installment; index: number; total: number; companyName: string }> = ({ sale, customer, installment, index, total, companyName }) => {
    return (
        <div className="bg-white text-black p-4 border border-dashed border-gray-400 flex flex-col justify-between text-xs break-inside-avoid-page">
            <div>
                <div className="flex justify-between items-center border-b border-gray-300 pb-2 mb-2">
                    <div>
                        <h2 className="font-bold text-sm">{companyName}</h2>
                        <p>Documento sem valor fiscal</p>
                    </div>
                    <div className="text-right">
                        <p>Vencimento</p>
                        <p className="font-bold text-sm">{new Date(installment.dueDate).toLocaleDateString('pt-BR')}</p>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                    <div>
                        <p className="text-gray-600">CLIENTE</p>
                        <p className="font-semibold">{customer.name}</p>
                    </div>
                     <div className="text-right">
                        <p className="text-gray-600">PARCELA</p>
                        <p className="font-bold text-lg">{`${index + 1}/${total}`}</p>
                    </div>
                </div>
                 <div className="text-right mb-4">
                    <p className="text-gray-600">VALOR</p>
                    <p className="font-bold text-xl">{formatCurrency(installment.amount)}</p>
                </div>
            </div>
            <div className="border-t border-gray-300 pt-2 text-gray-600">
                <p>Venda ID: {sale.id.substring(0, 8)}...</p>
                <p>Data da Compra: {new Date(sale.date).toLocaleDateString('pt-BR')}</p>
            </div>
        </div>
    );
};

const PaymentBooklet: React.FC<PaymentBookletProps> = ({ sale, customer, company, onClose }) => {
    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="fixed inset-0 bg-gray-700 bg-opacity-75 z-50 flex flex-col items-center p-4 print:p-0 print:bg-white printable-area">
            <style>
                {`
                @media print {
                    body * {
                        visibility: hidden;
                    }
                    .printable-area, .printable-area * {
                        visibility: visible;
                    }
                    .printable-area {
                        position: absolute;
                        left: 0;
                        top: 0;
                        width: 100%;
                        padding: 1cm;
                        box-sizing: border-box;
                    }
                    .print-controls {
                        display: none !important;
                    }
                    @page {
                        size: A4;
                        margin: 0;
                    }
                }
                `}
            </style>
            
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-xl print-controls w-full max-w-4xl mb-4">
                <div className="flex justify-between items-center">
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Carnê de Pagamento</h2>
                     <div className="flex gap-2">
                        <button onClick={handlePrint} className="flex items-center bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700 transition-colors">
                            <span className="material-symbols-outlined mr-2">print</span>
                            Imprimir
                        </button>
                        <button onClick={onClose} className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-2">
                            <span className="material-symbols-outlined text-3xl">close</span>
                        </button>
                     </div>
                </div>
            </div>

            <div id="booklet-content" className="bg-white p-4 w-full max-w-4xl h-full overflow-y-auto print:overflow-visible print:h-auto">
                 <div className="grid grid-cols-2 gap-4">
                     {sale.installments.map((inst, index) => (
                        <PaymentSlip
                            key={inst.id}
                            sale={sale}
                            customer={customer}
                            installment={inst}
                            index={index}
                            total={sale.installments.length}
                            companyName={company.name}
                        />
                     ))}
                </div>
                <div className="text-center text-gray-500 mt-4 text-xs print:hidden">
                    <p>Instruções: Para melhor resultado, configure a impressão para "Layout: Retrato" e "Margens: Nenhuma".</p>
                    <p>Cada folha A4 contém até 4 carnês. Recorte nas linhas pontilhadas.</p>
                </div>
            </div>
        </div>
    );
};

export default PaymentBooklet;