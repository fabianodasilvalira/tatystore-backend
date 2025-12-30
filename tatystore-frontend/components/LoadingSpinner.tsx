/**
 * Componente de Loading Reutilizável
 * 
 * Spinner de carregamento com tamanhos configuráveis
 */

import React from 'react';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    className?: string;
    message?: string;
}

const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
    xl: 'h-16 w-16 border-4',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
    size = 'md',
    className = '',
    message,
}) => {
    return (
        <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
            <div
                className={`animate-spin rounded-full border-primary-600 border-t-transparent ${sizeClasses[size]}`}
                role="status"
                aria-label="Carregando"
            />
            {message && (
                <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
            )}
        </div>
    );
};

/**
 * Componente de Loading para página inteira
 */
export const PageLoading: React.FC<{ message?: string }> = ({ message = 'Carregando...' }) => {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <LoadingSpinner size="xl" message={message} />
        </div>
    );
};

/**
 * Componente de Loading inline (para botões, etc)
 */
export const InlineLoading: React.FC = () => {
    return <LoadingSpinner size="sm" className="inline-block" />;
};
