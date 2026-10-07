# Atualização do SIGUS no servidor

Playbook **recorrente**. Instalação do zero: [docs/INSTALACAO.md](docs/INSTALACAO.md). IIS de Sorocaba: [docs/SETUP.md](docs/SETUP.md).

Ambiente: Windows, Flask + PostgreSQL, IIS + HttpPlatformHandler, prefixo `/sigus`. Produção: https://saudedigital.sorocaba.sp.gov.br/sigus

**Não** inventar dados de teste em produção (NSP, chamado, transferência, comunicado). **Não** commitar `.env`, dump nem upload. **Não** fazer `git push --force` no `main`.

Substitua `C:\inetpub\wwwroot\sigus` pelo caminho físico real do aplicativo no IIS.

Cursor no servidor: copie [PRODUCAO-CURSOR.md](PRODUCAO-CURSOR.md) para o chat daquela máquina.

---

> **Servidor de Sorocaba: nunca rode `iisreset` nem recicle o `DefaultAppPool`.** O mesmo IIS atende o **esussamu**, que não pode parar. Lá o IIS só faz proxy de `/sigus` para o processo `python run.py` na porta 5001; para publicar, reinicie **só esse processo** (seção 4).

## Entrega mais recente (veículos, RDV e reserva de salas na agenda)

Depois do `git pull`, com backup do banco feito antes:

```powershell
.\venv\Scripts\python.exe migrations\add_veiculos_reservas.py
```

Idempotente. Reinicie só o SIGUS (seção 4).

O que mudou:

- **Veículos com cadastro próprio** (tabela `veiculos`, sem ligação com equipamentos), na aba **Veículos** do detalhe da unidade: prefixo, check **Alugado** (aparece como **AL-383**) e locadora, placa, marca, modelo, categoria, ano, cor, combustível, lotação, RENAVAM, chassi, km no cadastro e vencimento do licenciamento. O formulário sugere ~100 modelos populares (Mobi, Onix, Strada, HB20, Hilux, Ducato, Sprinter, CG 160…) do catálogo `veiculo_modelos`. Nova seção de permissão **Veículos** (copiada de Equipamentos na migração).
- Se a versão anterior (veículo como tipo de equipamento) já tinha rodado, a migração remove o tipo "Veículo", as marcas de carro sem uso, o campo `eh_veiculo` e as salas/tipo "Garagem" vazias, e religa a agenda à tabela nova. Se houver equipamento cadastrado com o tipo Veículo, ela avisa e não apaga nada.
- Agenda com o tipo **Veículo**: quem vai usar, destino, bloqueio de horário duplicado, registro de quem agendou e km de saída/chegada na própria reserva.
- Página do veículo (`/sigus/veiculos/<id>`) com os usos do mês e o **RDV** no modal de impressão, igual ao "Mapa - Uso Diário do Veículo" oficial (A4 paisagem, frente e verso), preenchido com as reservas ou em branco.
- Tipos de sala com **Reservável na agenda** (Sala de Reunião AMB-41 e o novo Auditório já vêm marcados) e salas com **Disponível para todas as unidades**. Na agenda, o botão **Verificar salas vazias** mostra a unidade do evento, depois o mesmo prédio/endereço e depois o resto da rede; a reserva da sala também bloqueia horário duplicado.

Conferência: aba Veículos de uma unidade, agenda → Criar → Veículo, e agenda → Reunião → Verificar salas vazias.

---

## Entrega anterior (padrão de salas e equipamentos do Planejamento)

Depois do `git pull`, com backup do banco feito antes:

```powershell
.\venv\Scripts\python.exe migrations\add_padrao_salas.py
.\venv\Scripts\python.exe migrations\importar_padrao_salas.py
.\venv\Scripts\python.exe migrations\importar_padrao_salas.py --aplicar
```

A planilha não está no Git: coloque-a em `migrations\dados\padrao_salas_ubs.xlsx` ou passe `--planilha C:\caminho\arquivo.xlsx`. A primeira chamada da importação só simula e mostra o que vai mudar; a segunda grava. Ambas são idempotentes. Reinicie só o SIGUS (seção 4).

O que mudou:

- Os tipos de sala ganharam o código de ambiente padrão (`AMB-xx`) e o grupo da planilha do Planejamento. Tipos equivalentes foram renomeados para o nome do padrão; os genéricos (ex.: "Consultório") ficam sem código, para reclassificar.
- Os tipos de equipamento ganharam o catálogo de itens (`ITEM-xxx`, classificação, valor de referência, Base/Função). Foram criados os itens que não existiam (mobiliário, equipamentos médicos).
- Cada tipo de sala tem um **kit padrão** editável em Configurações → Tipos de Sala.
- Relatório novo **Padrão de Salas e Equipamentos** (`/sigus/relatorios/padrao-salas`) e aba **Padrão do ambiente** no detalhe da sala.
- Menu Configurações → **Padrão de Salas** (`/sigus/configuracoes/padrao-salas`): atalhos para editar ambientes, kits e itens; **Encaixar salas existentes** (reclassificação em lote com sugestão pelo nome); **Ligar inventário ao catálogo** ("conta como" dos tipos de equipamento já cadastrados). Sem migração.
- Kit com item **por profissional** (quantidade × máx. de profissionais simultâneos da sala) e relatório com **Painel** de situação do kit (completo, com itens a mais, incompleto, nenhum item). Rode de novo `migrations\add_padrao_salas.py` (cria a coluna `kit_padrao_sala.por_profissional`; idempotente) antes de reiniciar.

Detalhe: [docs/PADRAO_SALAS_EQUIPAMENTOS.md](docs/PADRAO_SALAS_EQUIPAMENTOS.md).

Conferência: abrir `/sigus/configuracoes/tipos-sala` (grupos AMB) e `/sigus/relatorios/padrao-salas` (33 UBS do padrão).

---

## Entrega anterior (Segurança do Paciente no fluxo do Núcleo, acesso público e QR code)

Depois do `git pull`:

```powershell
.\venv\Scripts\python.exe migrations\add_nsp_fluxo_nucleo.py
```

Migration idempotente. Reinicie só o SIGUS (seção 4).

O que mudou:

- **Segurança do Paciente** refeita no fluxo do SNI-SGQSP: qualquer pessoa notifica (com ou sem login, anônima por padrão); o Núcleo qualifica e encaminha às comissões das unidades; a coordenação só vê o que o Núcleo liberar. Auditoria anônima na notificação. Relatórios com painel. Detalhe: [docs/SEGURANCA_PACIENTE.md](docs/SEGURANCA_PACIENTE.md).
- **Acesso público + QR code** no padrão SIGUS: Links Úteis (endereço curto `/sigus/links`, público para quem não está logado, e QR de cada link), Cadastro Público, notificação de Segurança do Paciente e Mapa da Saúde. O cartão PNG quebra título e endereço sem cortar. Detalhe: [docs/MAPA_DO_CODIGO.md](docs/MAPA_DO_CODIGO.md#acesso-público-e-qr-code).
- **Links Úteis**: saíram os botões de filtro por seção; fica só a busca.
- **Agenda**: barras de vários dias no topo do dia, empurrando os demais eventos para baixo.

**Depois de publicar:** cadastre os membros do Núcleo em **Configurações → Segurança do Paciente**. Sem ninguém na lista, as notificações chegam mas ninguém as vê.

Conferência: abrir `/sigus/seguranca-paciente/notificar` numa aba anônima e notificar um caso fictício **só em ambiente de teste**; em produção, apenas abrir a tela. Baixar o QR em `/sigus/links/` e em `/sigus/relatorios/mapa-saude` e conferir o endereço `https://saudedigital.sorocaba.sp.gov.br/...` no cartão.

---

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

**Sorocaba (IIS compartilhado com o esussamu):** não toque no IIS. Reinicie só o processo do SIGUS.

Jeito recomendado, na raiz do projeto e com o mesmo Python que roda a produção:

```powershell
python scripts\_reiniciar_sigus.py
```

O script encerra o processo da porta 5001 **só se** a linha de comando dele contiver `run.py` (senão aborta), sobe o `run.py` de novo **em segundo plano, sem janela** (`FLASK_ENV=production`, `SIGUS_PORT=5001`) e espera `/sigus/login` responder. Resultado em `scripts\_reiniciar.log`; saída do servidor em `logs\sigus_5001.log`. Como não há janela, fechar uma janela não derruba o SIGUS.

Jeito manual, se o script não estiver disponível:

1. Descubra o PID na porta 5001: `netstat -ano -p TCP | findstr ":5001"`.
2. Confirme que é o SIGUS: `(Get-CimInstance Win32_Process -Filter "ProcessId=<PID>").CommandLine` precisa conter `run.py`. Se não contiver, **pare**.
3. `taskkill /PID <PID> /F` e espere a porta liberar.
4. Suba de novo na raiz do projeto com `FLASK_ENV=production` e `SIGUS_PORT=5001`: `python run.py`. Num console aberto, fechar a janela derruba o SIGUS.

Nunca: `iisreset`, reciclar o `DefaultAppPool`, matar `w3wp.exe` ou outro `python.exe`, editar o `web.config` do IIS.

**Outra instalação, com app pool próprio do SIGUS (HttpPlatformHandler):** recicle só o pool `sigus`.

Depois:

1. Abra `/sigus/login`.
2. Confira o módulo da entrega (ex.: Segurança do Paciente, Transferências, Relatórios).
3. Impressos devem abrir no **modal** padrão do SIGUS, não numa página crua.

Log: `.\logs\sigus_5001.log` (Sorocaba, pelo script de reinício) ou `.\logs\python.log` (HttpPlatformHandler).

---

## 5. Conferência rápida pós-deploy

- Login e seletor de unidade no topo
- Ficha de uma unidade (abas Salas / Equipamentos)
- Um chamado (abrir ou ver fila, conforme perfil)
- Se a entrega foi NSP: `/sigus/seguranca-paciente/` e Configurações → Segurança do Paciente
- Se a entrega foi patrimônio: `/sigus/transferencias/?aba=lojinha`

Manuais da ponta (Estante) são outro passo: [docs/MANUAIS_ESTANTE.md](docs/MANUAIS_ESTANTE.md).
