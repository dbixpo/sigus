# Banco de dados e migrations

## Motor

PostgreSQL. A URL está em `DATABASE_URL` no `.env` (nunca no Git). `config.py` aceita `postgres://` e normaliza para `postgresql://`.

Schema principal: **`public`** (SIGUS). Módulo de emendas/licitações do Patrick usa o schema **`sueq`** (ver `scripts/importar_schema_sueq.py` e `database/sueq_schema.sql`).

## Dump e restore

| Ação | Script | Observação |
|---|---|---|
| Exportar o banco da máquina atual | `python scripts/clone_banco.py` | Gera `database/sigus_backup_AAAAMMDD_HHMM.sql` — **gitignore** |
| Restaurar | `python scripts/restaura_banco.py` | Lê `database/sigus_backup.zip` ou o `.sql` mais recente; usa `DATABASE_URL` |

Dumps **não** entram no Git. Backup de cada instalação é da equipe que opera aquele servidor. **Não** commitar dump. **Não** restaurar um dump em cima de um banco que já atende gente sem cópia prévia.

Instalação nova, sem dado de outra rede: [INSTALACAO.md](INSTALACAO.md) (`migrations/bootstrap_nova_instalacao.py`).

## Levar esta instalação para outro computador

O código vem do Git. O banco **não**. No notebook:

1. Clone ou `git pull` deste repositório.
2. PostgreSQL local e um `.env` **novo**, com `DATABASE_URL` em `localhost`. `SIGUS_BEHIND_PROXY=0` e `SIGUS_PUBLIC_HOST` vazio. Não copie o `.env` do servidor.
3. Banco vazio: `python migrations/bootstrap_nova_instalacao.py` (cria as tabelas e, no fim, `add_inventario_catalogo.py`: RENEM, status de equipamento e itens de veículo).
4. Quer os dados de uma rede que já usa o SIGUS: faça o dump **naquela** máquina (`python scripts/clone_banco.py`) e restaure **aqui** (`python scripts/restaura_banco.py`). O dump não vai para o Git. Se o dump for anterior a 20/10/2026, rode `python migrations/add_inventario_catalogo.py` depois do restore.
5. Suba com `python run.py` em `http://localhost:5001/sigus/`. Não aponte este `.env` para o servidor.

## Trabalhar neste computador sem mexer numa instalação que já roda

O SIGUS lê **só** a `DATABASE_URL` do `.env` da pasta em que você está.

1. PostgreSQL instalado aqui. `CREATE DATABASE sigus;`
2. `.env` com `postgresql://postgres:senha@localhost:5432/sigus`
3. `SIGUS_BEHIND_PROXY=0` e `SIGUS_PUBLIC_HOST` vazio
4. Banco vazio: `migrations/bootstrap_nova_instalacao.py` e, se quiser o primeiro admin, `migrations/recriar_admin.py` **neste** banco
5. Subir com `run.py` e abrir `http://localhost:5001/sigus/`

Se a `DATABASE_URL` apontar para o host de um servidor, o `run.py` deste notebook grava naquele banco. Não faça isso. Não copie o `.env` do servidor para cá. Um dump, se existir, é um arquivo que você restaurou **no Postgres local** de propósito — e mesmo assim não volta para o Git.

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

3. Depois do `git pull` **no servidor da instalação**, rode **só os scripts novos** daquela entrega ([ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md)). No notebook, rode a mesma migration contra o Postgres local.
4. Não rode a pasta inteira “por garantia”: alguns scripts são one-shot de correção de dados (`reparar_realocacao_transferencias.py`, `backfill_…`, `recriar_admin.py`).

Catálogo e avisos: [migrations/README.md](../migrations/README.md).

Importação de dados por planilha: `migrations/importar_padrao_salas.py` lê `migrations/dados/padrao_salas_ubs.xlsx` (fora do Git) ou o arquivo de `--planilha`, simula por padrão e só grava com `--aplicar`. Ver [PADRAO_SALAS_EQUIPAMENTOS.md](PADRAO_SALAS_EQUIPAMENTOS.md).

## Models

SQLAlchemy em `app/models/`. Nova tabela = model + migration que cria a tabela. Num banco **já povoado**, o `create_all` **não** substitui a migration da entrega. Num **banco vazio**, o bootstrap chama `create_all` e em seguida os seeds — [INSTALACAO.md](INSTALACAO.md).

## Backup

Fica com quem opera a instalação (`pg_dump` agendado, do jeito da equipe). Este repositório **não** é o backup. Antes de mudança destrutiva (baixa em lote, migration de dados), faça dump **daquele** banco.
