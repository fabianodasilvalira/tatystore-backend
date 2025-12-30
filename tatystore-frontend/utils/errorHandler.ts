/**
 * Sistema de Tratamento de Erros Centralizado
 * 
 * Fornece funções para tratar erros de forma consistente em toda a aplicação
 */

import { logger } from './logger';

/**
 * Extrai mensagem de erro de diferentes formatos
 */
export const getErrorMessage = (error: any): string => {
    // Erro de API (FastAPI)
    if (error.response?.data?.detail) {
        return typeof error.response.data.detail === 'string'
            ? error.response.data.detail
            : 'Erro ao processar requisição';
    }

    // Erro de rede
    if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
        return 'Erro de conexão. Verifique sua internet.';
    }

    // Erro de timeout
    if (error.code === 'ECONNABORTED') {
        return 'Requisição demorou muito. Tente novamente.';
    }

    // Erro genérico
    return error.message || 'Erro desconhecido';
};

/**
 * Trata erro de API e retorna mensagem amigável
 */
export const handleApiError = (error: any, context: string): string => {
    const message = getErrorMessage(error);

    // Logar erro
    logger.apiError(error, context);

    return message;
};

/**
 * Trata erro de forma silenciosa (apenas loga)
 */
export const handleSilentError = (error: any, context: string): void => {
    logger.error('Silent error', error, context);
};

/**
 * Verifica se erro é de autenticação
 */
export const isAuthError = (error: any): boolean => {
    return error.response?.status === 401 || error.response?.status === 403;
};

/**
 * Verifica se erro é de validação
 */
export const isValidationError = (error: any): boolean => {
    return error.response?.status === 422 || error.response?.status === 400;
};
