import React from 'react';
import { InstallmentStatus } from '../types';
import { logger } from '../utils/logger';

interface InstallmentStatusBadgeProps {
    status: InstallmentStatus | string;
}

const InstallmentStatusBadge: React.FC<InstallmentStatusBadgeProps> = ({ status }) => {
    // Normaliza o status 'cancelled' (comum em algumas APIs) para 'canceled'
    const normalizedStatus = status === 'cancelled' ? 'canceled' : status;

    const statusInfo: { [key in InstallmentStatus]: { text: string; color: string } } = {
        paid: { text: 'Paga', color: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' },
        pending: { text: 'Pendente', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300' },
        overdue: { text: 'Atrasada', color: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300' },
        canceled: { text: 'Cancelada', color: 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200' },
    };

    const info = statusInfo[normalizedStatus as InstallmentStatus];

    // Se um status inesperado for recebido, exibe um placeholder para não quebrar a UI
    if (!info) {
        logger.warn(`Status de parcela desconhecido recebido: "${status}"`, undefined, 'InstallmentStatusBadge');
        return <span className="px-2 py-1 rounded-full text-xs font-semibold bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200">-</span>;
    }

    return <span className={`px-2 py-1 rounded-full text-xs font-semibold ${info.color}`}>{info.text}</span>;
};

export default InstallmentStatusBadge;