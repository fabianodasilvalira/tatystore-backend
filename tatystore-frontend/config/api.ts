/**
 * Configuração centralizada da API
 * 
 * Este arquivo centraliza todas as URLs da API para facilitar manutenção.
 * As URLs são lidas das variáveis de ambiente do Vite.
 */

// URL base do servidor (lida do .env via VITE_API_URL)
// Para desenvolvimento local: http://localhost:8080
// Para produção: https://tatystore.cloud
export const SERVER_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// URL base da API (adiciona /api/v1 ao servidor)
export const API_BASE_URL = `${SERVER_BASE_URL}/api/v1`;

/**
 * Converte uma URL relativa em URL completa
 * @param relativeOrFullUrl - URL relativa ou completa
 * @returns URL completa
 */
export const getFullUrl = (relativeOrFullUrl: string | undefined | null): string => {
    if (!relativeOrFullUrl) return '';

    // Se já é uma URL completa, retorna como está
    if (relativeOrFullUrl.startsWith('http://') || relativeOrFullUrl.startsWith('https://')) {
        return relativeOrFullUrl;
    }

    // Converte URL relativa em completa
    return `${SERVER_BASE_URL.replace(/\/$/, '')}/${relativeOrFullUrl.replace(/^\//, '')}`;
};

/**
 * Obtém URL completa de imagem com fallback para placeholder
 * @param relativeOrFullUrl - URL relativa ou completa da imagem
 * @param placeholder - URL do placeholder (opcional)
 * @returns URL completa da imagem ou placeholder
 */
export const getFullImageUrl = (
    relativeOrFullUrl: string | undefined | null,
    placeholder: string = 'https://placehold.co/600x600/f1f5f9/9ca3af?text=PrimeStore'
): string => {
    if (!relativeOrFullUrl) return placeholder;
    return getFullUrl(relativeOrFullUrl);
};
