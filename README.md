# SIGUS

**Sistema Integrado de Gestão das Unidades de Saúde.** Software livre de **Diego Bispo Fernandes** ([dbixpo](https://github.com/dbixpo)), licença [MIT](LICENSE).

O SIGUS é a gestão da unidade: patrimônio, chamados, planejamentos, agenda, pessoas, contratos, emendas, Segurança do Paciente e painéis do Metabase. **Não é prontuário.** O atendimento clínico continua no sistema clínico da rede.

| | |
|---|---|
| Código | https://github.com/dbixpo/sigus |
| Licença | [MIT](LICENSE) — Diego Bispo Fernandes |
| Stack | Python 3.10/3.11, Flask, PostgreSQL, IIS + HttpPlatformHandler |
| Entrada | `run.py` (Flask em desenvolvimento, Waitress atrás do IIS) |
| Prefixo | `/sigus` (`APPLICATION_ROOT`) |

Quem for assumir a manutenção começa por [docs/00_INDICE.md](docs/00_INDICE.md). Para subir uma cópia neste computador, sem falar com nenhum servidor que já esteja no ar, siga a seção abaixo e [docs/BANCO.md](docs/BANCO.md).

---

## Cópia local (neste computador)

Python 3.10 ou 3.11 e PostgreSQL **nesta máquina**. O `psql` precisa estar no PATH.

```powershell
git clone https://github.com/dbixpo/sigus.git
cd sigus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

No `.env` desta máquina:

- `DATABASE_URL` aponta para `localhost` (banco `sigus` local).
- `FLASK_ENV=development`
- `SIGUS_BEHIND_PROXY=0`
- `SIGUS_PUBLIC_HOST` fica vazio.
- `SECRET_KEY` pode ser qualquer texto longo. Não reutilize a chave de um servidor.

**Não** copie o `.env` de um servidor para cá. **Não** coloque na `DATABASE_URL` o host, a senha ou o nome do banco de uma instalação que já atende gente. Este computador fala só com o PostgreSQL local.

Banco vazio:

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe migrations\bootstrap_nova_instalacao.py
```

O primeiro administrador sai de `migrations/recriar_admin.py`, com `SIGUS_ADMIN_EMAIL` e `SIGUS_ADMIN_SENHA` definidos só nesta sessão do terminal. Esse script **apaga todos os administradores** do banco para o qual o `.env` aponta. Por isso ele só roda no banco local novo.

```powershell
$env:SIGUS_ADMIN_EMAIL = "voce@localhost"
$env:SIGUS_ADMIN_SENHA = "uma-senha-longa"
.\venv\Scripts\python.exe migrations\recriar_admin.py
.\venv\Scripts\python.exe run.py
```

Abra **http://localhost:5001/sigus/**.

Identidade da instalação (nome da secretaria, município, logos) fica em Configurações, gravada no banco local.

Base pronta, sem gente e sem senha de servidor: o arquivo `database/sigus_inicial.sql` traz unidades, catálogos e o dashboard 580 do Metabase, com a chave de incorporação vazia. Num clone novo, `scripts/restaura_banco.py` usa esse arquivo (um `sigus_backup_*.sql` local, se existir, tem prioridade e **não** vai para o Git).

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe scripts\restaura_banco.py
.\venv\Scripts\python.exe run.py
```

Entre com `admin@localhost` / `sigus-inicial` e troque a senha. Para os painéis, cole a chave em Configurações → Metabase. Não restaure esse arquivo por cima de um banco que já atende gente.

Se você tiver um dump **seu**, feito de propósito para desenvolvimento e sem obrigação de sigilo que impeça tê-lo nesta máquina:

```powershell
.\venv\Scripts\python.exe scripts\restaura_banco.py
```

O script lê `database/sigus_backup.zip` ou o `.sql` mais recente e restaura no banco da `DATABASE_URL` — de novo, a local.

---

## Documentação

A pasta [docs/](docs/00_INDICE.md) é o manual para quem for manter o sistema.

| Preciso… | Leia |
|---|---|
| Instalar do zero | [docs/INSTALACAO.md](docs/INSTALACAO.md) |
| Entender o que o sistema faz | [docs/01_VISÃO_GERAL.md](docs/01_VISÃO_GERAL.md) |
| Banco, dump, migrations, cópia de casa | [docs/BANCO.md](docs/BANCO.md) |
| Mexer no código | [docs/ARQUITETURA.md](docs/ARQUITETURA.md), [docs/MAPA_DO_CODIGO.md](docs/MAPA_DO_CODIGO.md) |
| Perfil e menu | [docs/PERMISSOES.md](docs/PERMISSOES.md) |
| Publicar num IIS | [docs/SETUP.md](docs/SETUP.md) |
| Atualizar um servidor que já roda | [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md) |
| Receber o sistema (checklist) | [docs/CHECKLIST_TRANSFERENCIA.md](docs/CHECKLIST_TRANSFERENCIA.md) |
| Senhas e integrações | [docs/SEGREDOS_E_INTEGRACOES.md](docs/SEGREDOS_E_INTEGRACOES.md) |
| Cores e logo | [docs/IDENTIDADE_VISUAL.md](docs/IDENTIDADE_VISUAL.md) |
| Painéis do Metabase | [docs/METABASE.md](docs/METABASE.md) |

Como alterar o código: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## O que nunca vai para o Git

- `.env`, senhas, `SECRET_KEY` de qualquer instalação
- Dumps `database/sigus_backup*.sql` / `*.zip`
- Uploads (`app/static/uploads/…`)
- Endereço, caminho de pasta ou nome de pool de um servidor que já está no ar
- `venv/`, `__pycache__/`, logs

Dado de pessoa não entra no repositório. O Git é o código. O banco de cada instalação fica na máquina dela.
