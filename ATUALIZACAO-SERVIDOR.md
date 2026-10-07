# Atualização do SIGUS no servidor

Playbook **recorrente**. Instalação do zero: [docs/INSTALACAO.md](docs/INSTALACAO.md). IIS de Sorocaba: [docs/SETUP.md](docs/SETUP.md).

Ambiente: Windows, Flask + PostgreSQL, IIS + HttpPlatformHandler, prefixo `/sigus`. Produção: https://saudedigital.sorocaba.sp.gov.br/sigus

**Não** inventar dados de teste em produção (NSP, chamado, transferência, comunicado). **Não** commitar `.env`, dump nem upload. **Não** fazer `git push --force` no `main`.

Substitua `C:\inetpub\wwwroot\sigus` pelo caminho físico real do aplicativo no IIS.

Cursor no servidor: copie [PRODUCAO-CURSOR.md](PRODUCAO-CURSOR.md) para o chat daquela máquina.

---

> **Servidor de Sorocaba: nunca rode `iisreset` nem recicle o `DefaultAppPool`.** O mesmo IIS atende o **esussamu**, que não pode parar. Lá o IIS só faz proxy de `/sigus` para o processo `python run.py` na porta 5001; para publicar, reinicie **só esse processo** (seção 4).

## Entrega de 07/10/2026 (ausência na agenda, frequência do RH, base de servidores)

Depois do `git pull`:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe migrations\add_agenda_ausencia.py
.\venv\Scripts\python.exe migrations\add_frequencia_rh.py
```

`requirements.txt` ganhou `xlrd` (lê a planilha `.xls`). As duas migrations são idempotentes. Reinicie só o SIGUS (seção 4).

O que mudou:

- **Agenda**: tipo **Ausência / férias**, visível para a unidade, com motivo privado. Quem está fora aparece como indisponível nas reuniões.
- **Importar frequência** (Configurações): gestores locais, centrais e administradores sobem a planilha mensal do RH. O SIGUS guarda os dados e descarta o arquivo; reimportar o mesmo mês e local substitui.
- **Recursos Humanos → Meus apontamentos**: cada profissional vê justificativas do mês, banco de horas e horas extras das suas matrículas. **Apontamentos da unidade** para gestores.
- **Base de servidores** (aba oculta Banco de Dados) e **Funções do RH × CBO** (Configurações → CBOs). No cadastro de usuário, a base sugere as matrículas e o CBO.
- Detalhe: [docs/FREQUENCIA_RH.md](docs/FREQUENCIA_RH.md).

Conferência: importar uma planilha em `/sigus/rh/frequencia/importar`, conferir a prévia e confirmar; abrir `/sigus/rh/apontamentos/unidade`; na agenda, criar uma ausência e ver a pessoa "fora" na disponibilidade de uma reunião.

---

## Entrega de 06/10/2026 (agenda, prazos, comunicados, aniversariantes)

Depois do `git pull`:

```powershell
.\venv\Scripts\python.exe migrations\add_comunicado_versao.py
```

Única migration desta entrega (idempotente). Agenda e prazos não mudam o banco.

O que mudou:

- **Agenda** no estilo Google: visões dia/semana/mês/lista, início e fim livres, "Dia inteiro", períodos de vários dias, arrastar para mudar data/horário/duração com **Desfazer**. Detalhe: [docs/AGENDA_E_PLANEJAMENTOS.md](docs/AGENDA_E_PLANEJAMENTOS.md).
- **Prazos de ações** podem ser alterados ou removidos (pela agenda ou por Planejamentos). Cada mudança vira observação no histórico da ação e notifica os responsáveis.
- **Comunicados e mural**: editar (só o autor) e excluir (autor ou administrador). Comunicado editado pede ciência de novo. Detalhe: [docs/COMUNICADOS.md](docs/COMUNICADOS.md).
- **Aniversariantes**: perfil administrador passa a aparecer.

Conferência: `/sigus/agenda/` (abrir e fechar vários eventos seguidos, arrastar um evento seu e desfazer), lápis de prazo em `/sigus/planejamentos/`, editar um comunicado próprio. Ctrl+F5 se o CSS antigo da agenda aparecer.

---

## Entrega anterior (ciência perfil OU CBO + tzdata)

Depois do `git pull`:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe migrations\add_ciencia_filtros.py
```

`tzdata` é obrigatório no Windows (`ZoneInfo` de Brasília). A migration só adiciona `ciencia_perfis` / `ciencia_cbos` se ainda não existirem. Reinicie o SIGUS (seção 4).

Conferência: **Novo comunicado** — título, texto, anexo, unidade, cobrar ciência, quem (equipe **ou** perfil **ou** CBO). A lista de CBO usa cadastro **e** matrícula ativa.

---

## 1. Código

```powershell
cd C:\inetpub\wwwroot\sigus
git status
git pull origin main
```

Se `git status` mostrar alteração local que vocês não esperavam, **pare** e resolva (stash, commit na TI, ou descarte com autorização). Não dê `reset --hard` sem backup.

Se o `requirements.txt` mudou:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Crie pastas de upload que o `.gitignore` omite, se ainda não existirem:

```powershell
New-Item -ItemType Directory -Force -Path app\static\uploads\nsp
New-Item -ItemType Directory -Force -Path app\static\uploads\chamados
New-Item -ItemType Directory -Force -Path app\static\uploads\identidade
New-Item -ItemType Directory -Force -Path app\static\uploads\comunicados
New-Item -ItemType Directory -Force -Path app\static\uploads\acoes
```

---

## 2. Banco (só o que a entrega pediu)

Na raiz, com o `.env` **de produção**:

```powershell
.\venv\Scripts\python.exe migrations\<script_desta_entrega>.py
```

Scripts são em geral idempotentes (`IF NOT EXISTS`). A lista **desta** entrega deve estar no PR ou no card.

Identidade da instalação (textos + galeria de assets):

```powershell
.\venv\Scripts\python.exe migrations\add_identidade_sistema.py
```

Dashboard da unidade + comunicados/mural de ações:

```powershell
.\venv\Scripts\python.exe migrations\add_noticias_mural.py
.\venv\Scripts\python.exe migrations\add_ciencia_auditoria.py
.\venv\Scripts\python.exe migrations\add_lojinha_destino.py
.\venv\Scripts\python.exe migrations\add_ciencia_cpf.py
.\venv\Scripts\python.exe migrations\add_mural_social.py
.\venv\Scripts\python.exe migrations\add_ciencia_filtros.py
```

### Já aplicados na rede (não precisa repetir, a menos que o banco seja novo)

Segurança do Paciente:

```
migrations\add_nsp.py
migrations\add_nsp_sis.py
migrations\add_nsp_tipos_infra.py
```

Agenda / feriados:

```
migrations\add_agenda.py
migrations\add_agenda_reunioes.py
migrations\add_feriados.py
```

Não rode `scripts/restaura_banco.py` nem dump `database/sigus_backup*.sql` em produção como “atualização”.

Não rode `migrations/recriar_admin.py` em produção.

---

## 3. `.env` (quando a entrega pedir variável nova)

Copie chaves **novas** do `.env.example` para o `.env` do servidor. Não versionar senha.

Integração SIS (busca de paciente no NSP) — só se o robô existir neste servidor:

```
SIS_CONSULTA_PATH=<pasta do repositório api-consulta-usuario-sis neste servidor>
SIS_USUARIO=
SIS_SENHA=
SIS_AMBIENTE=producao
SIS_SSL_VERIFY=true
```

Sem isso, o NSP continua abrindo: os campos de paciente ficam manuais.

Reinicie o processo do SIGUS depois de editar `.env` (seção 4; em Sorocaba, nunca o IIS).

---

## 4. Reinício

Templates e Python ficam em cache em produção: só aparecem depois de reiniciar. CSS/JS estáticos valem na hora (aumente o `?v=` no template).

**Sorocaba (IIS compartilhado com o esussamu):** não toque no IIS. Reinicie só o processo do SIGUS:

1. Descubra o PID na porta 5001: `netstat -ano -p TCP | findstr ":5001"`.
2. Confirme que é o SIGUS: `(Get-CimInstance Win32_Process -Filter "ProcessId=<PID>").CommandLine` precisa conter `run.py`. Se não contiver, **pare**.
3. `taskkill /PID <PID> /F` e espere a porta liberar.
4. Suba de novo na raiz do projeto, em console próprio, com `FLASK_ENV=production` e `SIGUS_PORT=5001`: `python run.py`.

Nunca: `iisreset`, reciclar o `DefaultAppPool`, matar `w3wp.exe` ou outro `python.exe`, editar o `web.config` do IIS.

**Outra instalação, com app pool próprio do SIGUS (HttpPlatformHandler):** recicle só o pool `sigus`.

Depois:

1. Abra `/sigus/login`.
2. Confira o módulo da entrega (ex.: Segurança do Paciente, Transferências, Relatórios).
3. Impressos devem abrir no **modal** padrão do SIGUS, não numa página crua.

Log: `.\logs\python.log`

---

## 5. Conferência rápida pós-deploy

- Login e seletor de unidade no topo
- Ficha de uma unidade (abas Salas / Equipamentos)
- Um chamado (abrir ou ver fila, conforme perfil)
- Se a entrega foi NSP: `/sigus/seguranca-paciente/` e Configurações → Segurança do Paciente
- Se a entrega foi patrimônio: `/sigus/transferencias/?aba=lojinha`

Manuais da ponta (Estante) são outro passo: [docs/MANUAIS_ESTANTE.md](docs/MANUAIS_ESTANTE.md).
