# Banco de Dados - Sistema SAMU 192

Estrutura e scripts para criação do banco de dados PostgreSQL.

## Estrutura

| Arquivo | Descrição |
|---------|-----------|
| `01_schema.sql` | Estrutura completa (CREATE TABLE) |
| `02_dados_iniciais.sql` | Dados iniciais (Unidade SAMU padrão) |
| `executar.py` | Script Python que cria banco, aplica schema, dados e admin |

## Executar tudo

**Requisito:** PostgreSQL em execução, usuário `postgres` com a senha configurada.

```bash
python database/executar.py
```

Ou, a partir da raiz do projeto:

```bash
cd c:\Users\hardr\Documents\Codes\samu
python database/executar.py
```

## Variáveis de ambiente (opcional)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_HOST` | localhost | Host do PostgreSQL |
| `DB_USER` | postgres | Usuário |
| `DB_PASSWORD` | @Qweszxc7895123 | Senha |
| `DB_NAME` | samu | Nome do banco |

## Resultado

- Banco `samu` criado (se não existir)
- Todas as tabelas criadas
- Unidade SAMU padrão "Central SAMU 192"
- Usuário admin: **administrador.sd** / **@Qweszxc7895123**

## Ordem manual (se preferir)

Se quiser executar os SQLs manualmente (via pgAdmin, DBeaver, psql):

1. Conectar ao PostgreSQL como `postgres`
2. `CREATE DATABASE samu;`
3. Conectar ao banco `samu`
4. Executar `01_schema.sql`
5. Executar `02_dados_iniciais.sql`
6. Inserir o admin manualmente (ou usar o `scripts/init_db.py` do projeto)
