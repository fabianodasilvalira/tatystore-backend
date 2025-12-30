/**
 * Sistema de Logging Centralizado
 * 
 * Em desenvolvimento: Loga no console
 * Em produção: Silencioso (pode ser integrado com serviços de monitoramento)
 */

type LogLevel = 'info' | 'warn' | 'error';

interface LogData {
    level: LogLevel;
    message: string;
    data?: any;
    timestamp: string;
    context?: string;
}

class Logger {
    private isDevelopment: boolean;

    constructor() {
        this.isDevelopment = import.meta.env.DEV;
    }

    private log(level: LogLevel, message: string, data?: any, context?: string) {
        const logData: LogData = {
            level,
            message,
            data,
            timestamp: new Date().toISOString(),
            context,
        };

        // Em desenvolvimento, logar no console
        if (this.isDevelopment) {
            const prefix = `[${level.toUpperCase()}]`;
            const contextStr = context ? ` [${context}]` : '';

            switch (level) {
                case 'info':
                    console.info(`${prefix}${contextStr} ${message}`, data || '');
                    break;
                case 'warn':
                    console.warn(`${prefix}${contextStr} ${message}`, data || '');
                    break;
                case 'error':
                    console.error(`${prefix}${contextStr} ${message}`, data || '');
                    break;
            }
        }

        // Em produção, enviar para serviço de monitoramento (futuro)
        // if (!this.isDevelopment) {
        //   this.sendToMonitoring(logData);
        // }
    }

    info(message: string, data?: any, context?: string) {
        this.log('info', message, data, context);
    }

    warn(message: string, data?: any, context?: string) {
        this.log('warn', message, data, context);
    }

    error(message: string, data?: any, context?: string) {
        this.log('error', message, data, context);
    }

    // Método auxiliar para logar erros de API
    apiError(error: any, context: string) {
        const message = error.response?.data?.detail || error.message || 'Erro desconhecido';
        this.error(`API Error: ${message}`, {
            status: error.response?.status,
            url: error.config?.url,
            method: error.config?.method,
        }, context);
    }
}

export const logger = new Logger();
