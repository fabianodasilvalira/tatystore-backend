/**
 * Error Boundary Component
 * 
 * Captura erros não tratados em componentes React
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { logger } from '../utils/logger';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
        };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        logger.error('React Error Boundary caught an error', {
            error: error.toString(),
            componentStack: errorInfo.componentStack,
        }, 'ErrorBoundary');
    }

    render() {
        if (this.state.hasError) {
            // Usar fallback customizado se fornecido
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Fallback padrão
            return (
                <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
                    <div className="max-w-md p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="material-symbols-outlined text-4xl text-red-600">error</span>
                            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                                Ops! Algo deu errado
                            </h1>
                        </div>

                        <p className="text-gray-600 dark:text-gray-400 mb-6">
                            Ocorreu um erro inesperado. Por favor, recarregue a página ou entre em contato com o suporte se o problema persistir.
                        </p>

                        {import.meta.env.DEV && this.state.error && (
                            <details className="mb-6">
                                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                                    Detalhes do erro (apenas em desenvolvimento)
                                </summary>
                                <pre className="mt-2 p-4 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-auto">
                                    {this.state.error.toString()}
                                </pre>
                            </details>
                        )}

                        <button
                            onClick={() => window.location.reload()}
                            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                        >
                            Recarregar Página
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
