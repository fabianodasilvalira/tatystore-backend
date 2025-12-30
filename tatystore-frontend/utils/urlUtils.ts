/**
 * Utilitários de URL
 * 
 * Funções centralizadas para manipulação de URLs
 */

/**
 * Converte URL relativa ou completa para URL completa
 * 
 * Regras:
 * - Se já for URL completa (http/https), retorna como está
 * - Se for /logo.png, retorna como está (asset do frontend)
 * - Caso contrário, adiciona o base URL da API
 */
export const getFullUrl = (
    relativeOrFullUrl: string | null | undefined,
    baseUrl?: string
): string => {
    if (!relativeOrFullUrl) return '';

    // URL completa
    if (relativeOrFullUrl.startsWith('http://') || relativeOrFullUrl.startsWith('https://')) {
        return relativeOrFullUrl;
    }

    // Logo da plataforma (asset do frontend)
    if (relativeOrFullUrl === '/logo.png') {
        return relativeOrFullUrl;
    }

    // URL relativa - adicionar base URL
    const base = baseUrl || import.meta.env.VITE_API_URL || '';
    return `${base.replace(/\/$/, '')}/${relativeOrFullUrl.replace(/^\//, '')}`;
};

/**
 * Extrai nome do arquivo de uma URL
 */
export const getFilenameFromUrl = (url: string | null | undefined): string => {
    if (!url) return '';

    try {
        const parts = url.split('/');
        return parts[parts.length - 1] || '';
    } catch {
        return '';
    }
};
