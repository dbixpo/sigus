# SIGUS

**Sistema Integrado de Gestão das Unidades de Saúde** — software livre da Secretaria da Saúde de Sorocaba (Saúde Digital), para outras prefeituras usarem e adaptarem.

O SIGUS é a “gestão da casa”: patrimônio, chamados, planejamentos, agenda, pessoas, contratos, emendas e Segurança do Paciente. **Não é prontuário.** O atendimento clínico continua no sistema da casa (em Sorocaba, o **SISWEB**).

| | |
|---|---|
| Referência em produção | https://saudedigital.sorocaba.sp.gov.br/sigus |
| Código | https://github.com/dbixpo/sigus |
| Licença | [MIT](LICENSE) — Prefeitura Municipal de Sorocaba / Secretaria da Saúde |
| Manuais da ponta (Sorocaba) | [Estante SES](https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sigus) |
| Stack | Python 3.10/3.11, Flask, PostgreSQL, IIS + HttpPlatformHandler |
| Entrada | `run.py` (Waitress em produção, Flask debug em desenvolvimento) |
| Prefixo | Sempre `/sigus` (`APPLICATION_ROOT`) |

**Município novo:** comece por [docs/INSTALACAO.md](docs/INSTALACAO.md) (banco vazio, primeiro admin, identidade).  
**TI assumindo a instância de Sorocaba:** [docs/00_INDICE.md](docs/00_INDICE.md) e [checklist de transferência](docs/CHECKLIST_TRANSFERENCIA.md).

---

## Desenvolvimento local (Windows)

Python 3.10 ou 3.11, PostgreSQL local, `psql` no PATH.

```powershell
git clone https://github.com/dbixpo/sigus.git
cd sigus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env`: `SECRET_KEY`, `DATABASE_URL`, `SIGUS_PORT=5001`, `SIGUS_BEHIND_PROXY=0` no notebook sem IIS.

**Banco vazio (recomendado para outro município):**

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe migrations\bootstrap_nova_instalacao.py
```

Crie o primeiro administrador só nesse banco novo (`migrations/recriar_admin.py` com `SIGUS_ADMIN_EMAIL` e `SIGUS_ADMIN_SENHA`). Detalhes: [docs/INSTALACAO.md](docs/INSTALACAO.md).

**Quem já tem dump da própria rede:**

```powershell
.\venv\Scripts\python.exe scripts\restaura_banco.py
.\venv\Scripts\python.exe run.py
```

Abra **http://localhost:5001/sigus/** (o prefixo `/sigus` também vale no localhost).

Produção no IIS: [docs/SETUP.md](docs/SETUP.md). Atualização: [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md).

---

## Documentação

A pasta [docs/](docs/00_INDICE.md) é o manual técnico para a TI.

| Preciso… | Leia |
|---|---|
| Instalar do zero (qualquer município) | [docs/INSTALACAO.md](docs/INSTALACAO.md) |
| Entender o que o sistema faz | [docs/01_VISÃO_GERAL.md](docs/01_VISÃO_GERAL.md) |
| Mexer no código / blueprints | [docs/ARQUITETURA.md](docs/ARQUITETURA.md), [docs/MAPA_DO_CODIGO.md](docs/MAPA_DO_CODIGO.md) |
| Entender perfil e menu | [docs/PERMISSOES.md](docs/PERMISSOES.md) |
| Banco, dump, migrations | [docs/BANCO.md](docs/BANCO.md), [migrations/README.md](migrations/README.md) |
| Comunicados e ciência | [docs/COMUNICADOS.md](docs/COMUNICADOS.md) |
| Subir ou atualizar o servidor | [docs/SETUP.md](docs/SETUP.md), [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md) |
| Cores, logo, padrão visual | [docs/IDENTIDADE_VISUAL.md](docs/IDENTIDADE_VISUAL.md) |
| Senhas, SIS, Estante | [docs/SEGREDOS_E_INTEGRACOES.md](docs/SEGREDOS_E_INTEGRACOES.md) |
| Manuais para o usuário final | [docs/MANUAIS_ESTANTE.md](docs/MANUAIS_ESTANTE.md) |

Como contribuir: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## O que nunca vai para o Git

- `.env`, senhas, `SECRET_KEY`
- Dumps `database/sigus_backup*.sql` / `*.zip` com dado real
- Uploads (`app/static/uploads/…`)
- `venv/`, `__pycache__/`, logs

Não publique dump de produção nem cadastro de profissionais. LGPD vale para o código **e** para o banco.

---

## Origem

Sistema da **Secretaria da Saúde de Sorocaba / Saúde Digital**, licenciado em MIT para que outras prefeituras possam implantar e adaptar. Mantenha o aviso de copyright. A paleta e a marca SIGUS estão em [docs/IDENTIDADE_VISUAL.md](docs/IDENTIDADE_VISUAL.md).
