# Atualização no servidor (SIGUS) — Segurança do Paciente

Instruções para o agente no servidor da Saúde Digital. Objetivo: puxar o `main` do GitHub, aplicar as migrations do NSP, configurar a consulta SIS no `.env` (sem versionar senha) e reiniciar o app.

Este módulo é **novo**. Já foi testado no computador de desenvolvimento. No servidor, só aplicar o que está neste arquivo. **Não** inventar notificações de teste em produção. **Não** commitar dumps, uploads nem `.env`. **Não** fazer `push --force`.

## 1. Código

Na pasta do repositório SIGUS (`C:\Users\hardr\Documents\GitHub\sigus` ou o caminho equivalente neste servidor):

```
git status
git pull origin main
```

Se houver alteração local que não deve perder, avisar o usuário antes de descartar.

O `requirements.txt` ganhou `requests` e `beautifulsoup4`. Reinstalar no venv:

```
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Criar a pasta de anexos se ainda não existir (está no `.gitignore`):

```
New-Item -ItemType Directory -Force -Path app\static\uploads\nsp
```

## 2. Banco de dados (PostgreSQL)

Rodar **na raiz do repositório**, com o venv do SIGUS, nesta ordem:

```
.\venv\Scripts\python.exe migrations\add_nsp.py
.\venv\Scripts\python.exe migrations\add_nsp_sis.py
.\venv\Scripts\python.exe migrations\add_nsp_tipos_infra.py
```

Os scripts são idempotentes (`IF NOT EXISTS` / `ON CONFLICT DO NOTHING`).

### O que cada um faz

**`migrations/add_nsp.py`**
- Cria `nsp_catalogos` (listas configuráveis dos selects).
- Cria `nsp_ocorrencias` (notificação da unidade, protocolo `SP-AAAA-NNNNN`).
- Cria `nsp_anexos`, `nsp_andamentos`, `nsp_encaminhamentos`, `nsp_acoes`.
- Adiciona `notificacoes.nsp_ocorrencia_id` (nullable).
- Insere catálogos iniciais (status, classificação, tipos de incidente, setores de UBS, destinos).
- Libera a seção `SegurancaPaciente` em `perfil_permissoes`.

**`migrations/add_nsp_sis.py`**
- Colunas `cpf` e `cns` em `nsp_ocorrencias`.
- Ajusta o rótulo da classificação “Quase erro” (sem termo em inglês).

**`migrations/add_nsp_tipos_infra.py`**
- Inclui os tipos de incidente de falta de sistema/energia/internet, infraestrutura e recursos (ICPS-OMS / Anvisa).

Não rodar dump `database/sigus_backup.sql` neste passo.

Se as migrations de agenda/feriados **ainda não** rodaram neste servidor, rode antes (também idempotentes):

```
.\venv\Scripts\python.exe migrations\add_agenda.py
.\venv\Scripts\python.exe migrations\add_agenda_reunioes.py
.\venv\Scripts\python.exe migrations\add_feriados.py
```

## 3. Consulta ao SIS (`.env` do servidor)

A tela de nova notificação busca paciente no SISWEB (CPF, CNS ou prontuário) pelo robô `api-consulta-usuario-sis`. Sem isso, o formulário ainda funciona: os campos abrem para preencher na mão.

No `.env` do SIGUS **neste servidor** (nunca no Git), conferir/incluir:

```
SIS_CONSULTA_PATH=C:\Users\hardr\Documents\GitHub\api-consulta-usuario-sis
SIS_USUARIO=
SIS_SENHA=
SIS_AMBIENTE=producao
SIS_SSL_VERIFY=true
```

- **Não** commitar senha. **Não** colar senha em commit, log ou chat.
- Se o usuário já passou as credenciais neste ambiente, usar as do `.env` local de desenvolvimento **só neste servidor**, copiando para o `.env` de produção. Se não tiver, pedir ao usuário.
- A pasta `SIS_CONSULTA_PATH` precisa existir neste computador. Se não existir, avisar o usuário (não inventar outro caminho). O repositório costuma ficar em `C:\Users\hardr\Documents\GitHub\api-consulta-usuario-sis`.
- Depois de editar o `.env`, o processo Flask/IIS precisa reiniciar para ler as variáveis.

## 4. Reiniciar o aplicativo

O SIGUS neste computador roda em Flask + PostgreSQL, em produção atrás de IIS/HttpPlatformHandler (prefixo `/sigus`).

1. Reiniciar o site no IIS (ou o processo `python run.py` se for o ambiente de teste).
2. Abrir `/sigus/seguranca-paciente/` (menu **Gestão da Unidade → Segurança do Paciente**).
3. Conferir **Configurações → Segurança do Paciente** (listas dos selects, inclusive “Falta de sistema, energia ou internet”).
4. Conferir o botão **Imprimir** na ficha: deve abrir o **modal** de impresso do SIGUS (não uma página crua).
5. Não abrir notificação de teste em produção, salvo o usuário pedir.

## 5. O que mudou no sistema (para conferir)

- **Segurança do Paciente**: a unidade abre a própria notificação, com protocolo, classificação, ação imediata, anexos (10 MB), linha do tempo, plano de ação e encaminhamento a outros setores.
- Investigação da Anvisa (etapas 5–10) no detalhe; óbito, dano grave e evento que nunca deveria ocorrer **não encerram** sem essas etapas.
- Na nova notificação: tipo de pessoa primeiro; se for paciente, busca no SIS por CPF, CNS ou prontuário; se o SIS não achar, campos abertos.
- Interface **sem termo em inglês** (quase erro, jamais deveria ocorrer).
- Campo opcional de número/data do **Notivisa** (não envia para a Anvisa; só registra se já foi notificado lá).
- Relatórios e exportação Excel/CSV; card em Relatórios.
- Aba na ficha da unidade.
- Permissão nova: seção **Segurança do Paciente** (Ver / Editar / Adicionar) em Gestão de Perfis.

Arquivos principais: `app/models/nsp.py`, `app/routes/nsp.py`, `app/sis_consulta.py`, `app/templates/nsp/`, `migrations/add_nsp.py`, `docs/SEGURANCA_PACIENTE.md`.

Se o import `nsp_bp` falhar, conferir se o `pull` trouxe `app/routes/nsp.py` e o model.
