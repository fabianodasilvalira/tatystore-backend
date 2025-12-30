/**
 * Utilitários de Data
 * 
 * Funções centralizadas para manipulação de datas
 */

import { logger } from './logger';

/**
 * Converte string/Date para Date de forma segura
 * Retorna null se a conversão falhar
 */
export const safeParseDate = (dateInput: string | Date | null | undefined): Date | null => {
    if (!dateInput) return null;

    try {
        if (dateInput instanceof Date) {
            return isNaN(dateInput.getTime()) ? null : dateInput;
        }

        const parsed = new Date(dateInput);
        if (isNaN(parsed.getTime())) {
            logger.warn(`Failed to parse date string: "${dateInput}"`, undefined, 'dateUtils');
            return null;
        }

        return parsed;
    } catch (error) {
        logger.error('Error parsing date', { dateInput, error }, 'dateUtils');
        return null;
    }
};

/**
 * Formata data para exibição (DD/MM/YYYY)
 */
export const formatDate = (date: Date | string | null | undefined): string => {
    const parsed = safeParseDate(date);
    if (!parsed) return '-';

    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    }).format(parsed);
};

/**
 * Formata data e hora para exibição (DD/MM/YYYY HH:mm)
 */
export const formatDateTime = (date: Date | string | null | undefined): string => {
    const parsed = safeParseDate(date);
    if (!parsed) return '-';

    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(parsed);
};

/**
 * Verifica se data está vencida
 */
export const isOverdue = (date: Date | string | null | undefined): boolean => {
    const parsed = safeParseDate(date);
    if (!parsed) return false;

    return parsed < new Date();
};
