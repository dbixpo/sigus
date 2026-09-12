# Migrations (scripts one-shot)

Pasta `migrations/`. São programas Python, não revisões Alembic. Rode **um arquivo por vez**, na raiz do repositório, com o `.env` do banco que você quer alterar.

```powershell
.\venv\Scripts\python.exe migrations\add_nsp.py
```

A maioria imprime o que fez e pode ser reexecutada.

## Não rode em produção (salvo pedido explícito com backup)

| Script | Por quê |
|---|---|
| `recriar_admin.py` | **Apaga todos os administradores** e cria um novo. Senha só por variável de ambiente. Prefira `scripts/reset_usuario_sigus.py` |
| `reparar_realocacao_transferencias.py` | Correção pontual de dados |
| `backfill_*.py` | Preenche colunas a partir de dado legado; rode só se a entrega pedir |
| `limpar_chamado_atribuidos.py` | Limpeza de dados |

## Módulos recentes (referência)

Se o servidor ainda **não** tem o objeto, estes são os scripts típicos (já idempotentes):

**Segurança do Paciente**

- `add_nsp.py` — tabelas, catálogos, permissão
- `add_nsp_sis.py` — CPF/CNS, rótulos
- `add_nsp_tipos_infra.py` — tipos de incidente de infraestrutura

**Agenda**

- `add_agenda.py`
- `add_agenda_reunioes.py`
- `add_feriados.py`

**Transferências / Lojinha**

- `add_documentos_transferencia.py`
- `add_itens_lojinha.py`

**Patrimônio**

- `add_capacidade_maxima_salas.py`

Lista completa: os arquivos `add_*.py` nesta pasta. O nome descreve o que entra no banco.

## Convenção para script novo

```python
# migrations/add_exemplo.py
"""Cria … (idempotente)."""
# conectar via create_app() ou psycopg2 + DATABASE_URL
# CREATE TABLE IF NOT EXISTS …
# ALTER TABLE … ADD COLUMN IF NOT EXISTS …
print('OK')
```

Documente o arquivo no PR e, se for produção, acrescente a linha de comando em `ATUALIZACAO-SERVIDOR.md` **desta** entrega.
