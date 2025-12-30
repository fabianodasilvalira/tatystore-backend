# Prompt para Geração de Backend para Sistema de Perfumaria (Donna Parfum)

## Objetivo Principal

Criar um backend robusto e completo, utilizando a stack de tecnologia especificada, para servir como API para a aplicação de gerenciamento de perfumaria "Donna Parfum". O frontend já foi desenvolvido e este backend deve suprir todas as suas necessidades de dados e lógica de negócios.

## Stack de Tecnologia

*   **Linguagem/Framework**: Node.js com **NestJS**. O projeto deve ser gerado com o NestJS CLI, utilizando TypeScript.
*   **Banco de Dados**: **PostgreSQL**.
*   **ORM**: **TypeORM**. Para mapeamento objeto-relacional e interações com o banco de dados.
*   **Containerização**: **Docker** e **Docker Compose**. O ambiente de desenvolvimento e produção deve ser totalmente containerizado.

## Estrutura do Banco de Dados

Implemente o seguinte esquema de banco de dados. Crie as entidades TypeORM correspondentes para cada uma das tabelas abaixo, configurando os relacionamentos (OneToMany, ManyToOne, etc.) corretamente.

### 1. Tabela: `customers`
| Coluna | Tipo de Dado (PostgreSQL) | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` | **Chave Primária**. |
| `name` | `VARCHAR(255)` | Nome completo. (Obrigatório) |
| `phone` | `VARCHAR(20)` | Telefone. |
| `address` | `TEXT` | Endereço. |
| `cpf` | `VARCHAR(14)` | CPF. (Único) |
| `status` | `VARCHAR(10)` | 'active' ou 'inactive'. (Obrigatório) |
| `created_at` | `TIMESTAMPTZ` | Data de criação. |
| `updated_at` | `TIMESTAMPTZ` | Data de atualização. |

### 2. Tabela: `products`
| Coluna | Tipo de Dado (PostgreSQL) | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` | **Chave Primária**. |
| `name` | `VARCHAR(255)` | Nome. (Obrigatório) |
| `brand` | `VARCHAR(100)` | Marca. |
| `description` | `TEXT` | Descrição. |
| `price` | `NUMERIC(10, 2)`| Preço de venda. |
| `stock` | `INTEGER` | Estoque. (Obrigatório) |
| `photo_url` | `TEXT` | URL da foto. |
| `status` | `VARCHAR(10)` | 'active' ou 'inactive'. (Obrigatório) |
| `created_at` | `TIMESTAMPTZ` | Data de criação. |
| `updated_at` | `TIMESTAMPTZ` | Data de atualização. |

### 3. Tabela: `sales`
| Coluna | Tipo de Dado (PostgreSQL) | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` | **Chave Primária**. |
| `customer_id` | `UUID` | **Chave Estrangeira** (`customers(id)`). |
| `total_amount` | `NUMERIC(10, 2)`| Valor total. (Obrigatório) |
| `payment_method`| `VARCHAR(10)` | 'cash' ou 'credit'. (Obrigatório) |
| `sale_date` | `TIMESTAMPTZ` | Data da venda. (Obrigatório) |
| `first_due_date`| `DATE` | Vencimento da 1ª parcela (crediário). |
| `status` | `VARCHAR(15)` | 'completed' ou 'canceled'. (Obrigatório) |
| `created_at` | `TIMESTAMPTZ` | Data de criação. |
| `updated_at` | `TIMESTAMPTZ` | Data de atualização. |

### 4. Tabela: `sale_items`
| Coluna | Tipo de Dado (PostgreSQL) | Descrição |
| :--- | :--- | :--- |
| `sale_id` | `UUID` | **Chave Estrangeira** (`sales(id)`). |
| `product_id` | `UUID` | **Chave Estrangeira** (`products(id)`). |
| `quantity` | `INTEGER` | Quantidade. (Obrigatório) |
| `unit_price` | `NUMERIC(10, 2)`| Preço unitário no momento da venda. (Obrigatório) |

### 5. Tabela: `installments`
| Coluna | Tipo de Dado (PostgreSQL) | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` | **Chave Primária**. |
| `sale_id` | `UUID` | **Chave Estrangeira** (`sales(id)`). |
| `amount` | `NUMERIC(10, 2)`| Valor da parcela. (Obrigatório) |
| `due_date` | `DATE` | Vencimento. (Obrigatório) |
| `status` | `VARCHAR(10)` | 'pending', 'paid', 'overdue'. (Obrigatório) |
| `created_at` | `TIMESTAMPTZ` | Data de criação. |
| `updated_at` | `TIMESTAMPTZ` | Data de atualização. |


## Funcionalidades e Endpoints da API (RESTful)

Crie módulos no NestJS para cada recurso principal, implementando os seguintes endpoints com validação de dados de entrada (usando `class-validator` e `class-transformer`).

### 1. Módulo: `Products` (`/products`)
*   `POST /`: Criar um novo produto.
*   `GET /`: Listar todos os produtos. Permitir filtros por `status` e busca por `name` e `brand`.
*   `GET /:id`: Obter detalhes de um produto específico.
*   `PUT /:id`: Atualizar um produto. Inclui a capacidade de alterar o status (ativar/desativar).
*   `DELETE /:id`: (Opcional, considere a desativação como a prática padrão).

### 2. Módulo: `Customers` (`/customers`)
*   `POST /`: Criar um novo cliente.
*   `GET /`: Listar todos os clientes. Permitir filtros por `status` e busca por `name`.
*   `GET /:id`: Obter detalhes de um cliente específico. Deve incluir um resumo de suas dívidas.
*   `PUT /:id`: Atualizar um cliente. Inclui a capacidade de alterar o status.

### 3. Módulo: `Sales` (`/sales`)
*   `POST /`: Registrar uma nova venda. Este é o endpoint mais complexo:
    *   Recebe `customerId`, uma lista de `items` (com `productId` e `quantity`), `paymentMethod`, e, se for crediário, `numInstallments` e `firstDueDate`.
    *   **Lógica de Negócio**:
        1.  Validar se há estoque suficiente para todos os produtos.
        2.  Calcular o `total_amount` da venda.
        3.  Criar o registro na tabela `sales`.
        4.  Criar os registros correspondentes na tabela `sale_items`.
        5.  **Debitar** a quantidade vendida do estoque na tabela `products`.
        6.  Se o `paymentMethod` for `credit`, calcular e criar todos os registros na tabela `installments`.
*   `GET /`: Listar todas as vendas, com informações básicas do cliente associado.
*   `GET /:id`: Obter detalhes completos de uma venda, incluindo itens e parcelas.
*   `PUT /:id/cancel`: Cancelar uma venda.
    *   **Lógica de Negócio**:
        1.  Mudar o `status` da venda para 'canceled'.
        2.  **Restaurar** o estoque dos produtos que foram vendidos.

### 4. Módulo: `Installments` (`/installments`)
*   `PUT /:id/pay`: Marcar uma parcela como 'paga'.

### 5. Módulo: `Reports` (`/reports`)
Crie endpoints para alimentar os relatórios do frontend.
*   `GET /reports/sales-summary`: Retorna dados agregados de vendas (receita total, número de vendas) com base em filtros de data (hoje, semana, mês, período customizado).
*   `GET /reports/overdue-customers`: Retorna uma lista de clientes com parcelas atrasadas e o valor total devido.
*   `GET /reports/low-stock`: Retorna uma lista de produtos com estoque baixo (ex: <= 5 unidades).

## Lógica de Negócios Adicional

*   Crie um serviço (possivelmente com um `CronJob` usando `@nestjs/schedule`) que executa diariamente para verificar as parcelas (`installments`) com `status` 'pending' e `due_date` anterior à data atual, atualizando seu `status` para 'overdue'.

## Configuração do Ambiente (Docker)

*   **`Dockerfile`**: Crie um `Dockerfile` otimizado (multi-stage build) para a aplicação NestJS.
*   **`docker-compose.yml`**: Crie um arquivo `docker-compose.yml` que orquestre dois serviços:
    1.  `api`: O serviço da aplicação NestJS.
    2.  `db`: O serviço do banco de dados PostgreSQL.
    *   Configure volumes para a persistência dos dados do PostgreSQL.
    *   Use variáveis de ambiente (`.env` file) para configurar a conexão com o banco de dados e outras configurações sensíveis.

## Entregáveis Esperados

1.  Código-fonte completo da aplicação NestJS.
2.  `Dockerfile` e `docker-compose.yml` configurados.
3.  Um arquivo `.env.example` com as variáveis de ambiente necessárias.
4.  Um `README.md` detalhado explicando:
    *   Como configurar o ambiente e rodar o projeto com `docker-compose up`.
    *   Uma breve documentação dos endpoints da API (pode ser gerada automaticamente com o Swagger do NestJS).