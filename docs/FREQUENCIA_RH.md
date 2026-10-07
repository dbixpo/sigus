# Frequência do RH, apontamentos e base de servidores

Todo mês cada unidade preenche a planilha de frequência (`.xls`/`.xlsx`) e manda ao RH. O SIGUS lê essa planilha, guarda os dados no banco e **descarta o arquivo**. Cada profissional passa a consultar os próprios apontamentos: justificativas do mês, banco de horas e horas extras, com quem lançou.

Código:

- Leitura da planilha: `app/services/frequencia_planilha.py` (`ler_planilha`)
- Base do RH e CBO: `app/services/base_rh.py`
- Modelos e siglas: `app/models/frequencia.py`
- Rotas: `app/routes/frequencia.py` (blueprint `frequencia`, prefixo `/rh`)
- Telas: `app/templates/rh/apontamentos*.html`, `rh/frequencia_*.html`, `rh/servidores.html`, `configuracoes/cbos/funcoes_rh.html`
- CSS: `app/static/css/frequencia.css`
- Migration: `migrations/add_frequencia_rh.py`. Dependência: `xlrd` (lê `.xls`); `.xlsx` usa `openpyxl`.

## Quem faz o quê

| Quem | Pode |
|---|---|
| Qualquer usuário logado | **Meus apontamentos** (`/rh/apontamentos`): só as próprias matrículas |
| Gestor local: perfil Gestor de Área, ou papel `gestor_principal`/`gestor_secundario` na unidade | Importar planilhas e ver **Apontamentos da unidade** das suas unidades. Também abre os apontamentos de quem aparece nelas |
| Gestor central (`gestor_secretaria`) e administrador | Tudo, de todas as unidades. Também o de-para de locais |
| Quem cadastra usuários | **Base de servidores** e a sugestão de matrícula/CBO no cadastro |

Regra em `unidades_gestao_rh(usuario)` (`None` = todas) e `Usuario.pode_importar_frequencia`.

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

- **Base de servidores** (`/rh/servidores`): busca por nome ou matrícula, mostra função, local, CBO sugerido e se já tem cadastro no SIGUS.
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
- `xlrd` 2.x só lê `.xls`. Se alguém salvar como `.xlsx`, quem lê é o `openpyxl` (`data_only`).
- Fórmulas sem valor salvo chegam como `0`: por isso `_txt` descarta números em campos de texto.
