# Testes Faltantes - Priority List

## 🔴 CRÍTICOS (Devem estar em produção)

### 1. User Management
\`\`\`
[ ] test_create_user_success
[ ] test_create_user_duplicate_email
[ ] test_list_users_own_company
[ ] test_update_user_success
[ ] test_delete_user_soft_delete
[ ] test_user_without_role_cannot_access
\`\`\`

### 2. Customer Management
\`\`\`
[ ] test_create_customer_success
[ ] test_list_customers_own_company_only
[ ] test_update_customer_success
[ ] test_delete_customer_soft_delete
[ ] test_cannot_access_customer_other_company
\`\`\`

### 3. Security Edge Cases
\`\`\`
[ ] test_sale_with_negative_discount
[ ] test_negative_stock_prevention
[ ] test_concurrent_sales_same_product
[ ] test_email_case_insensitive
[ ] test_duplicate_cnpj_rejected
\`\`\`

### 4. Token Management
\`\`\`
[ ] test_refresh_token_success
[ ] test_refresh_token_expired
[ ] test_logout_invalidates_token
[ ] test_token_expired_401
[ ] test_invalid_token_401
\`\`\`

### 5. Password Management
\`\`\`
[ ] test_change_password_success
[ ] test_change_password_wrong_current
[ ] test_password_weak_rejected
[ ] test_password_min_8_chars
[ ] test_password_same_as_current
\`\`\`

## 🟡 ALTOS (Importante para produção)

### 6. PIX Integration
\`\`\`
[ ] test_configure_pix_success
[ ] test_generate_qrcode_success
[ ] test_upload_pix_receipt_success
[ ] test_receipt_invalid_format_rejected
[ ] test_pix_isolation_by_company
\`\`\`

### 7. Relatórios Completos
\`\`\`
[ ] test_sales_report_with_date_range
[ ] test_profit_report_calculation
[ ] test_top_selling_products
[ ] test_canceled_sales_report
[ ] test_reports_export_csv
\`\`\`

### 8. Estoque Avançado
\`\`\`
[ ] test_stock_history_tracking
[ ] test_low_stock_notification
[ ] test_reabastecimento_workflow
[ ] test_estoque_zerado
[ ] test_atualizar_produto_afeta_vendas
\`\`\`

### 9. Installments Avançado
\`\`\`
[ ] test_juros_compostos
[ ] test_multa_por_atraso
[ ] test_parcela_antecipada_desconto
[ ] test_renegociacao_parcelas
[ ] test_notificacao_vencimento
\`\`\`

## 🟠 MÉDIOS (Nice to have)

### 10. Rate Limiting & Security
\`\`\`
[ ] test_brute_force_protection
[ ] test_rate_limiting_5_attempts
[ ] test_login_attempt_tracking
[ ] test_captcha_after_3_fails
[ ] test_account_lockout
\`\`\`

### 11. Auditoria
\`\`\`
[ ] test_audit_log_creation
[ ] test_audit_log_query
[ ] test_user_action_tracked
[ ] test_data_change_tracked
\`\`\`

### 12. Performance
\`\`\`
[ ] test_10k_vendas_relatório
[ ] test_1000_produtos_listagem
[ ] test_cron_10k_parcelas_performance
[ ] test_concurrent_10_users
\`\`\`

## Contagem

- Críticos: 20 testes
- Altos: 18 testes
- Médios: 12 testes
- **Total: 50 testes adicionais**

**Coverage final esperada: ~95%**
