# Guia de Uso: Importação em Massa de Produtos

## 📋 Visão Geral

A ferramenta de importação em massa permite cadastrar centenas de produtos de uma vez usando um arquivo CSV. Ideal para cadastrar produtos de marcas como Natura, Boticário e Eudora que precisam de ajuste de preços antes de serem ativados.

## 🚀 Como Usar

### Passo 1: Acessar a Ferramenta

1. Faça login no sistema
2. Acesse **Estoque** no menu lateral
3. Clique no botão **"Importar"** (ícone de upload)

### Passo 2: Baixar o Template

1. Na página de importação, clique em **"Baixar Template CSV"**
2. O template será baixado com:
   - Cabeçalhos corretos
   - Exemplos de produtos
   - Categorias da sua empresa
   - Instruções de preenchimento

### Passo 3: Preencher o CSV

Abra o arquivo CSV no Excel, Google Sheets ou editor de texto e preencha com seus produtos:

#### Campos Obrigatórios

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `nome` | Nome do produto | Batom Natura 001 |
| `marca` | Marca do produto | Natura |
| `categoria` | Categoria (deve existir no sistema) | Maquiagem |
| `preco_custo` | Preço de custo | 15.50 |
| `preco_venda` | Preço de venda | 35.90 |

#### Campos Opcionais

| Campo | Descrição | Padrão | Exemplo |
|-------|-----------|--------|---------|
| `descricao` | Descrição detalhada | vazio | Batom vermelho intenso |
| `estoque` | Quantidade em estoque | 0 | 10 |
| `estoque_minimo` | Estoque mínimo | 0 | 5 |
| `sku` | Código SKU | gerado automaticamente | NAT-BAT-001 |
| `codigo_barras` | Código de barras | vazio | 7891234567890 |
| `ativo` | Produto ativo? | false | false |
| `em_promocao` | Em promoção? | false | true |
| `preco_promocional` | Preço promocional | vazio | 29.90 |

### Passo 4: Dicas de Preenchimento

#### ✅ Produtos Pendentes de Ajuste de Preço

Para produtos que você ainda vai ajustar os preços:

```csv
nome,marca,categoria,preco_custo,preco_venda,ativo
Batom Natura 001,Natura,Maquiagem,0.01,0.01,false
Perfume Boticário XYZ,Boticário,Perfumaria,0.01,0.01,false
```

- Use `ativo=false` para que **não apareçam na vitrine**
- Use preços temporários (ex: 0.01)
- Depois ajuste os preços na área administrativa

#### ✅ Formato de Números

Aceita tanto **vírgula** quanto **ponto**:
- ✅ `15.50`
- ✅ `15,50`

#### ✅ Formato de Booleanos

Para campos `ativo` e `em_promocao`, aceita:
- ✅ `true` / `false`
- ✅ `sim` / `não`
- ✅ `1` / `0`
- ✅ `s` / `n`

#### ✅ Categorias

- A categoria deve existir no sistema
- Use o nome **exatamente** como está cadastrado
- O template mostra as categorias disponíveis

### Passo 5: Fazer Upload

1. Arraste o arquivo CSV para a área de upload **OU**
2. Clique na área de upload para selecionar o arquivo
3. Verifique se o arquivo foi selecionado corretamente
4. Clique em **"Importar Produtos"**

### Passo 6: Revisar Relatório

Após a importação, você verá:

#### ✅ Resumo
- Total de linhas processadas
- Quantidade de sucessos
- Quantidade de erros

#### ✅ Produtos Criados
- Lista dos produtos importados com sucesso
- Nome e SKU de cada produto

#### ✅ Erros (se houver)
- Número da linha com erro
- Descrição do erro
- Opção de exportar erros em CSV

### Passo 7: Ajustar Preços

Após importar produtos inativos:

1. Vá para **Estoque**
2. Marque **"Mostrar inativos"**
3. Edite cada produto individualmente
4. Ajuste preços e estoque
5. Marque como **ativo**
6. Produto aparece automaticamente na vitrine

## 🎯 Casos de Uso

### Caso 1: Cadastrar 500 Produtos Natura

**Objetivo:** Cadastrar produtos mas ajustar preços depois

**Solução:**
```csv
nome,marca,categoria,preco_custo,preco_venda,estoque,ativo
Batom Natura 001,Natura,Maquiagem,0.01,0.01,0,false
Batom Natura 002,Natura,Maquiagem,0.01,0.01,0,false
...
```

**Resultado:**
- ✅ 500 produtos cadastrados
- ✅ Não aparecem na vitrine (inativos)
- ✅ Você ajusta preços com calma
- ✅ Ativa quando estiver pronto

### Caso 2: Importar Produtos com Promoção

**Objetivo:** Cadastrar produtos já em promoção

**Solução:**
```csv
nome,marca,categoria,preco_custo,preco_venda,em_promocao,preco_promocional,ativo
Perfume Boticário XYZ,Boticário,Perfumaria,45.00,120.00,true,99.90,true
```

**Resultado:**
- ✅ Produto cadastrado ativo
- ✅ Aparece na seção de promoções
- ✅ Preço riscado na vitrine

### Caso 3: Atualizar Estoque em Massa

**Objetivo:** Cadastrar produtos com estoque inicial

**Solução:**
```csv
nome,marca,categoria,preco_custo,preco_venda,estoque,estoque_minimo,ativo
Creme Eudora ABC,Eudora,Cuidados,25.00,65.00,50,10,true
```

**Resultado:**
- ✅ Produto com estoque definido
- ✅ Alerta quando estoque < 10

## ⚠️ Erros Comuns

### Erro: "Categoria não encontrada"

**Causa:** Nome da categoria está diferente do cadastrado

**Solução:**
1. Baixe o template novamente
2. Veja as categorias disponíveis
3. Use o nome exatamente igual

### Erro: "Campo obrigatório"

**Causa:** Faltou preencher nome, marca, categoria ou preços

**Solução:**
1. Verifique a linha do erro
2. Preencha todos os campos obrigatórios

### Erro: "Preço inválido"

**Causa:** Preço não é um número válido

**Solução:**
- Use apenas números e ponto/vírgula
- Exemplo: `15.50` ou `15,50`

### Erro: "Arquivo muito grande"

**Causa:** Arquivo CSV maior que 5MB

**Solução:**
1. Divida em múltiplos arquivos menores
2. Importe em lotes

## 💡 Dicas Avançadas

### Gerar SKU Automaticamente

Deixe o campo `sku` vazio e o sistema gera automaticamente:

**Formato:** `{CATEGORIA}-{PRODUTO}-{SEQUENCIAL}`

**Exemplo:** `MAQ-BATO-001`

### Importar em Lotes

Para muitos produtos:
1. Divida em arquivos de 100-200 produtos
2. Importe um por vez
3. Revise erros entre cada lote

### Exportar Erros

Se houver muitos erros:
1. Clique em **"Exportar Erros"**
2. Corrija no CSV original
3. Importe novamente

## 📊 Limites

- **Tamanho máximo:** 5MB por arquivo
- **Produtos por importação:** Ilimitado (mas recomendado 500 por vez)
- **Formato:** Apenas CSV (UTF-8 ou Latin-1)

## 🔒 Segurança

- ✅ Apenas Admin e Gerente podem importar
- ✅ Produtos vinculados automaticamente à sua empresa
- ✅ Validação de todos os campos
- ✅ Transação única (tudo ou nada em caso de erro crítico)

## 📞 Suporte

Problemas com a importação?

1. Verifique se o CSV está no formato correto
2. Baixe o template novamente
3. Revise os erros no relatório
4. Entre em contato com o suporte se persistir
