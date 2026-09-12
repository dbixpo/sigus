# SIGUS

**Sistema Integrado de Gestão das Unidades de Saúde** da Secretaria da Saúde de Sorocaba (Saúde Digital).

O SIGUS é a “gestão da casa”: patrimônio, chamados, planejamentos, agenda, pessoas, contratos, emendas e Segurança do Paciente. **Não é prontuário.** O atendimento clínico continua no **SISWEB**.

| | |
|---|---|
| Produção | https://saudedigital.sorocaba.sp.gov.br/sigus |
| Código | https://github.com/dbixpo/sigus (repositório **privado**) |
| Manuais da ponta | [Estante SES — Manuais de utilização do SIGUS](https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sigus) |
| Stack | Python 3.10/3.11, Flask, PostgreSQL, IIS + HttpPlatformHandler |
| Entrada da app | `run.py` (Waitress em produção, Flask debug em desenvolvimento) |
| Prefixo | Sempre `/sigus` (`APPLICATION_ROOT`) |

Se você está recebendo este repositório para manter: comece por [docs/00_INDICE.md](docs/00_INDICE.md) e pelo [checklist de transferência](docs/CHECKLIST_TRANSFERENCIA.md).

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

Edite o `.env`: `SECRET_KEY`, `DATABASE_URL`, `SIGUS_PORT=5001`. Crie o banco `sigus` e restaure o dump (o ZIP **não** vai para o Git — peça o backup à equipe):

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe scripts\restaura_banco.py
.\venv\Scripts\python.exe run.py
```

Abra **http://localhost:5001/sigus/** (o prefixo `/sigus` também vale no localhost).

Detalhes, IIS e atualização de produção: [docs/SETUP.md](docs/SETUP.md) e [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md).

---

## Documentação

A pasta [docs/](docs/00_INDICE.md) é o manual técnico para a TI. Resumo:

| Preciso… | Leia |
|---|---|
| Entender o que o sistema faz | [docs/01_VISÃO_GERAL.md](docs/01_VISÃO_GERAL.md) |
| Mexer no código / blueprints | [docs/ARQUITETURA.md](docs/ARQUITETURA.md), [docs/MAPA_DO_CODIGO.md](docs/MAPA_DO_CODIGO.md) |
| Entender perfil e menu | [docs/PERMISSOES.md](docs/PERMISSOES.md) |
| Banco, dump, migrations | [docs/BANCO.md](docs/BANCO.md), [migrations/README.md](migrations/README.md) |
| Subir ou atualizar o servidor | [docs/SETUP.md](docs/SETUP.md), [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md) |
| Cores, logo, padrão visual | [docs/IDENTIDADE_VISUAL.md](docs/IDENTIDADE_VISUAL.md) |
| Senhas, SIS, Estante | [docs/SEGREDOS_E_INTEGRACOES.md](docs/SEGREDOS_E_INTEGRACOES.md) |
| Manuais para o usuário final | [docs/MANUAIS_ESTANTE.md](docs/MANUAIS_ESTANTE.md) |

Como contribuir (mesmo internamente): [CONTRIBUTING.md](CONTRIBUTING.md).

---

## O que nunca vai para o Git

- `.env`, senhas, `SECRET_KEY`
- Dumps `database/sigus_backup*.sql` (o `.zip` de desenvolvimento é exceção pontual; dumps novos **não** se commitam)
- Uploads (`app/static/uploads/…`)
- `venv/`, `__pycache__/`, logs

---

## Propriedade

Sistema da **Secretaria da Saúde de Sorocaba / Saúde Digital**. Repositório privado. Não publicar, não abrir fork público, não copiar dump de produção para máquina pessoal sem autorização.
