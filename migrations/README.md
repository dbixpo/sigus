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

Banco vazio (outro município): `migrations/bootstrap_nova_instalacao.py` — ver [docs/INSTALACAO.md](../docs/INSTALACAO.md).

Se o servidor ainda **não** tem o objeto, estes são os scripts típicos (já idempotentes):

**Segurança do Paciente**

- `add_nsp.py` — tabelas, catálogos, permissão
- `add_nsp_sis.py` — CPF/CNS, rótulos
- `add_nsp_tipos_infra.py` — tipos de incidente de infraestrutura

**Agenda**

- `add_agenda.py`
- `add_agenda_reunioes.py`
- `add_feriados.py`
- `add_agenda_ausencia.py` — coluna `motivo` (tipo Ausência / férias)

**Frequência do RH**

- `add_frequencia_rh.py` — importações, lançamentos, horas extras, base de servidores, de-para de locais e função × CBO

**Transferências / Lojinha**

- `add_documentos_transferencia.py`
- `add_itens_lojinha.py`

**Patrimônio**

- `add_inventario_catalogo.py` — colunas de incorporação, classificação RENEM (incluindo Veículos), status em `status_de_equipamento` e itens de veículo da RENEM. O bootstrap de banco vazio já chama este arquivo. Não carrega a planilha da Flávia.
- `add_categorias_equipamento.py` — mesma classificação, para banco que já tinha tipos com o texto antigo em `classificacao`
- `aplicar_catalogo_flavia.py` / `importar_itens_flavia.py` — carga da planilha desta rede (caminho local, fora do Git). Não rode num município novo.
- `add_capacidade_maxima_salas.py`
- `add_padrao_salas.py` — código/grupo nos tipos de sala, catálogo nos tipos de equipamento, `kit_padrao_sala`, código do imóvel da unidade
- `importar_padrao_salas.py` — carrega a planilha do Planejamento (`dados/padrao_salas_ubs.xlsx`, fora do Git, ou `--planilha`); simula sem `--aplicar`. Ver [docs/PADRAO_SALAS_EQUIPAMENTOS.md](../docs/PADRAO_SALAS_EQUIPAMENTOS.md)

**Identidade da instalação**

- `add_identidade_sistema.py` — textos (município, secretaria, domínio de e-mail) e galeria de assets; texto neutro se a linha 1 não existir (não sobrescreve instalação que já tem identidade)

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
