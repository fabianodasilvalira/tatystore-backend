"""
Mensagens centralizadas do sistema em português
Facilita manutenção e internacionalização
"""

class Messages:
    """Classe com todas as mensagens do sistema em português"""
    
    # Mensagens gerais
    SUCCESS = "Operação realizada com sucesso"
    RESOURCE_NOT_FOUND = "Recurso não encontrado"
    UNAUTHORIZED = "Não autorizado"
    
    # Parcelas (Installments)
    INSTALLMENT_NOT_FOUND = "Parcela não encontrada"
    INSTALLMENT_ALREADY_PAID = "Parcela já está paga"
    INSTALLMENT_CANCELLED = "Parcela está cancelada"
    INSTALLMENT_INVALID_STATUS = "Status inválido. Use: pending, paid, overdue, cancelled"
    
    # Pagamentos de Parcelas (Installment Payments)
    PAYMENT_CREATED = "Pagamento registrado com sucesso"
    PAYMENT_AMOUNT_REQUIRED = "Valor do pagamento é obrigatório e deve ser maior que zero"
    PAYMENT_AMOUNT_EXCEEDS = "Valor de pagamento (R$ {amount:.2f}) excede o saldo restante (R$ {remaining:.2f})"
    PAYMENT_INSTALLMENT_ID_REQUIRED = "installment_id é obrigatório"
    
    # Vendas (Sales)
    SALE_CANCELLED = "Venda cancelada com sucesso"
    
    # Clientes (Customers)
    CUSTOMER_NOT_FOUND = "Cliente não encontrado"
    
    # Usuários (Users)
    USER_NOT_FOUND = "Usuário não encontrado"
    WEAK_PASSWORD = "Nova senha fraca: {message}"
    PASSWORD_CHANGED = "Senha alterada com sucesso"
    
    # Autenticação (Auth)
    LOGOUT_SUCCESS = "Logout realizado com sucesso"
    
    # Empresas (Companies)
    COMPANY_CREATED = "Empresa criada com sucesso! URL da loja: {url}. Use as credenciais acima para primeiro acesso."
    
    # PIX
    PIX_KEY_CONFIGURED = "Chave PIX configurada com sucesso"
    PIX_QR_GENERATED = "QR Code gerado com sucesso. Apresente ao cliente para leitura."
    PIX_RECEIPT_REGISTERED = "Comprovante PIX registrado com sucesso"
    
    # Cron Jobs
    OVERDUE_INSTALLMENTS_UPDATED = "Parcelas vencidas atualizadas"
    
    @staticmethod
    def format(message: str, **kwargs) -> str:
        """Helper para formatar mensagens com parâmetros"""
        return message.format(**kwargs)
