# Frequência do RH, apontamentos e base de servidores

Todo mês cada unidade preenche a planilha de frequência (`.xls`, `.xlsx` ou `.ods`) e manda ao RH. O SIGUS lê essa planilha, guarda os dados no banco e **descarta o arquivo**. Cada profissional passa a consultar os próprios apontamentos: justificativas do mês, banco de horas e horas extras, com quem lançou.

Código:

- Leitura da planilha: `app/services/frequencia_planilha.py` (`ler_planilha`)
- Base do RH e CBO: `app/services/base_rh.py`
- Modelos e siglas: `app/models/frequencia.py`
- Rotas: `app/routes/frequencia.py` (blueprint `frequencia`, prefixo `/rh`)
- Telas: `app/templates/rh/apontamentos*.html`, `rh/frequencia_*.html`, `configuracoes/cbos/funcoes_rh.html`
- CSS: `app/static/css/frequencia.css`
- Migration: `migrations/add_frequencia_rh.py`. Dependência: `xlrd` (lê `.xls`); `.xlsx` usa `openpyxl`; `.ods` é lido direto do XML do LibreOffice.
- Falta abonada: cada dia `FA` da aba Justificativas (ou o total da Capa, se o dia não vier marcado) aparece na prévia e, depois de importar, na tela **Faltas abonadas**. Data igual à do perfil fica como lançada na frequência. Data que ainda não existe no perfil entra na conta do ano (limite de 6), sem criar o registro sozinha.

## Quem faz o quê

| Quem | Pode |
|---|---|
| Qualquer usuário logado | **Meus apontamentos** (`/rh/apontamentos`): só as próprias matrículas |
| Gestor de Área | Importar planilha e ver **Apontamentos da unidade** das unidades do próprio vínculo. A lista mostra só o arquivo que ele mesmo subiu. Abre o apontamento de quem está nessa planilha |
| Gestor central e administrador | A mesma tela, com o seletor de qualquer unidade ativa. Também só o arquivo que a própria pessoa importou. O de-para de locais continua com esses dois |
| Apoio administrativo e operador | Não entram em Apontamentos da unidade nem na importação. Meus apontamentos segue pessoal |

A tela usa o perfil efetivo (`administrador`, `gestor_secretaria`, `coordenador`). Trocar de unidade não mostra planilha de outra pessoa. Quem não importou nada vê a lista vazia. A sugestão de matrícula/CBO no cadastro de usuários continua para quem cadastra usuário, a partir da aba oculta da planilha.

## Planilha: o que é lido

Tudo é ligado pela **matrícula** (`normalizar_matricula`: só dígitos, sem zeros à esquerda). Nomes e funções fora da Capa são fórmulas sem valor salvo, por isso o nome vem da Capa ou da aba Banco de Dados.

| Aba | Vira |
|---|---|
| Capa | competência (`JULHO/2026`), local (`SES - UBS FIORE`), uma linha por matrícula: função, regime, condição, tipo (horário/mensal), HM, vencimento, totais em dias |
| Justificativas | sigla por dia (`{"7": "DCM"}`) e a coluna **Complemento** (férias e afastamentos em texto livre) |
| Horarios | horário de trabalho |
| Banco de Horas | saldo anterior, realizadas, utilizadas, saldo atual, observação |
| Horas Extras | HE 50 %, HE 100 %, HE 50 % noturna, HE 100 % noturna (podem ser de quem é de outra lotação) |
| Banco de Dados (oculta) | base de servidores: matrícula, nome, função, local |

Vencimento: horista em horas, mensalista em dias. Siglas e cores: `SIGLAS_JUSTIFICATIVA` (holerite = azul, legal = verde, desconto = vermelho).

## Importar (Configurações → Importar frequência)

1. Envia o arquivo (até 15 MB). A leitura vai para `instance/tmp_frequencia/<token>.json` (só o próprio usuário abre; apagado ao confirmar ou depois de 2 h).
2. **Prévia**: competência, local, profissionais, banco de horas, horas extras e avisos:
   - já existe importação desse mês e local (vai substituir);
   - conta do banco que não fecha (anterior + realizadas − utilizadas ≠ atual);
   - saldo anterior diferente do saldo atual do mês passado já importado;
   - matrículas que ainda não estão no cadastro de ninguém.
3. Escolhe a **unidade do SIGUS** (sugestão pelo nome; a escolha fica gravada em `rh_locais`).
4. Confirma. A chave é **competência + local**: reimportar marca a anterior como `substituida` (guarda quem e quando) e apaga as linhas dela.
5. A base de servidores (`rh_servidores`) é atualizada; planilha de mês mais antigo não sobrescreve dado mais novo.
6. Quem tem a matrícula no cadastro recebe a notificação `apontamentos`.

Excluir uma importação (histórico na mesma tela) tira os apontamentos dela da consulta.

## Meus apontamentos

- Seletor de competência (setas e lista) e uma aba por matrícula.
- Cartões: saldo do banco (último informado até o mês), dias com justificativa, horas extras do mês e do ano.
- Calendário do mês com as siglas, legenda com a contagem, complemento, horário, vencimento e totais da capa. Cada bloco mostra de qual unidade veio e quem importou.
- Horas extras por unidade que lançou, com o acumulado do ano.
- Banco de horas mês a mês com conferência: "Confere", "Conta não fecha" ou "Saldo anterior diferente do mês passado".
- Gestor abre a de outra pessoa por `?matricula=` (link na tela da unidade).

## Base de servidores e CBO

- A listagem da base fica em **Relatórios → Base de servidores do RH** (`/relatorios/base-rh`): uma matrícula por linha, com nome, função e local da planilha de competência mais nova. Sem competência na URL, abre a última. A aba oculta continua alimentando a sugestão de matrícula no cadastro de usuário (`GET /rh/servidores/buscar`).
- **Funções do RH × CBO** (Configurações → CBOs → aba): de-para `rh_funcao_cbo`. Sugestão automática pelo nome (`sugerir_cbo`); nada é gravado sem clicar em **Salvar de-para**.
- **Cadastro de usuário**: ao digitar o nome (ou importar pelo CPF), aparecem as matrículas da base com esse nome. As marcadas são criadas ao salvar (`cadastrar_matriculas_rh`): vínculo empregatício, estatutário, CBO do de-para. Matrícula que já é de outra pessoa não pode ser marcada.
- **Modal de matrícula**: ao digitar o número, mostra nome, função e local da base e preenche o CBO se estiver vazio.
- JSON usado pelas telas: `GET /rh/servidores/buscar?q=&limite=&usuario_id=`.

## Locais do RH × unidades

`/rh/frequencia/locais` (gestor central e administrador): liga cada local do RH (ex.: `SES - PA CARANDA - ENFERMAGEM`) a uma unidade. Vários locais podem apontar para a mesma unidade. A tela já vem com sugestões pelo nome; confira antes de salvar.

## Tabelas

`rh_locais`, `rh_servidores`, `rh_funcao_cbo`, `freq_importacoes`, `freq_lancamentos`, `freq_horas_extras`. Criadas por `migrations/add_frequencia_rh.py` (idempotente).

## Armadilhas

- Abas e cabeçalhos são achados pelo nome sem acento (`_norm`); a aba "Instruções" é ignorada.
- `xlrd` 2.x só lê `.xls`. `.xlsx` usa o `openpyxl` (`data_only`). `.ods` usa o valor já calculado pelo LibreOffice (`office:value`); se a planilha foi salva sem recalcular, os totais da Capa podem vir vazios.
- Fórmulas sem valor salvo chegam como `0`: por isso `_txt` descarta números em campos de texto.
