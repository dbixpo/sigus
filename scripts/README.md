# Scripts de operação

Rode na **raiz** do repositório, com venv e `.env`. Nenhum script deve receber senha commitada.

| Script | Uso |
|---|---|
| `scripts/clone_banco.py` | `pg_dump` → `database/sigus_backup_*.sql` (gitignore) |
| `scripts/restaura_banco.py` | Restaura ZIP ou SQL em `database/` no banco do `.env` |
| `scripts/reset_usuario_sigus.py` | Troca senha e/ou perfil. Ferramenta correta para admin perdido |
| `scripts/pub_estante_sigus.py` | Publica/atualiza o livro de manuais na Estante SES (capítulos gerais) |
| `scripts/pub_estante_patrimonio.py` | Capítulo patrimônio (salas, equipamentos, transferências, lojinha) |
| `scripts/importar_schema_sueq.py` | Importa schema/dados SUEQ para o schema `sueq` (não mexe no `public`) |

## Reset de senha

```powershell
.\venv\Scripts\python.exe scripts\reset_usuario_sigus.py --email alguem@sorocaba.sp.gov.br --nova-senha "SenhaForteAqui"
```

Não cole a senha em issue, chat ou commit.

## Estante SES

Credenciais só no ambiente: `ESTANTE_EMAIL`, `ESTANTE_SENHA`. Prints: pasta temporária `app/static/uploads/manuais_tmp/` (gitignore). Ver [docs/MANUAIS_ESTANTE.md](../docs/MANUAIS_ESTANTE.md).

## SUEQ

Dump original do Patrick **não** versionar. `database/sueq_schema.sql` e `sueq_seed.sql` são o recorte que o SIGUS usa. Uploads SUEQ em `app/static/uploads/sueq/` (gitignore).
