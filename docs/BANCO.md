# Banco de dados e migrations

## Motor

PostgreSQL. A URL está em `DATABASE_URL` no `.env` (nunca no Git). `config.py` aceita `postgres://` e normaliza para `postgresql://`.

Schema principal: **`public`** (SIGUS). Módulo de emendas/licitações do Patrick usa o schema **`sueq`** (ver `scripts/importar_schema_sueq.py` e `database/sueq_schema.sql`).

## Dump e restore

| Ação | Script | Observação |
|---|---|---|
| Exportar o banco da máquina atual | `python scripts/clone_banco.py` | Gera `database/sigus_backup_AAAAMMDD_HHMM.sql` — **gitignore** |
| Restaurar | `python scripts/restaura_banco.py` | Lê `database/sigus_backup.zip` ou o `.sql` mais recente; usa `DATABASE_URL` |

O arquivo `database/sigus_backup.zip` no Git é um **snapshot de desenvolvimento**, não substitui backup de produção. **Não** commitar dump novo. **Não** restaurar dump de homologação em cima de produção sem backup prévio.

Dump antigo com nomes `planos` / `acoes_plano`: depois do restore rode `python migrations/alinhar_nomenclatura_banco.py`.

## Como o schema evolui

Não usamos `flask db migrate` no fluxo da casa. Cada mudança vira um arquivo:

```
migrations/add_algo_descritivo.py
```

Regras:

1. **Idempotente**: `IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `ON CONFLICT DO NOTHING`.
2. Roda na **raiz do repo**, com venv e `.env` apontando para o banco alvo:

   ```powershell
   .\venv\Scripts\python.exe migrations\add_algo_descritivo.py
   ```

3. Depois do `git pull` em produção, rode **só os scripts novos** desta entrega (anote no PR e no [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md)).
4. Não rode a pasta inteira “por garantia”: alguns scripts são one-shot de correção de dados (`reparar_realocacao_transferencias.py`, `backfill_…`, `recriar_admin.py`).

Catálogo e avisos: [migrations/README.md](../migrations/README.md).

## Models

SQLAlchemy em `app/models/`. Nova tabela = model + migration que cria a tabela. O `create_all` **não** é o processo de produção.

## Backups de produção

Ficam a cargo da TI (pg_dump agendado / política da Prefeitura). Este repositório **não** é o backup. Depois de mudança destrutiva (baixa em lote, migration de dados), faça dump **antes**.
