# Agenda e prazos de planejamento

Agenda da unidade no estilo Google Agenda: eventos, reuniões com participantes, feriados e os prazos das ações de planejamento no mesmo calendário.

Código:

- Agenda: `app/routes/agenda.py`, `app/models/agenda.py`, `app/templates/agenda/calendario.html`, `app/static/css/agenda.css`
- Prazos: `app/routes/planejamentos.py` (`alterar_prazo_acao`, rota `atualizar_prazo_acao`), `app/templates/planejamentos/listar.html`
- Biblioteca: FullCalendar 6.1.15 (bundle global, com o plugin de interação)

## Tela

- Barra lateral com botão **Criar**, minicalendário, filtros (eventos e reuniões, prazos, feriados) e legenda. Abaixo de 1200 px ela vira gaveta.
- Visões: **Dia**, **Semana**, **Mês** e **Lista**. A última visão usada fica salva no navegador.
- Atalhos: `T` hoje, `D`/`S`/`M`/`L` visões, `J`/`K` avançar/voltar, `C` criar.
- Clicar num item abre a leitura. Editar e excluir ficam no topo do modal.
- Modais e confirmações são do próprio sistema (`abrirModal`, `confirmar`, `snack`). Não use `confirm()`/`alert()` do navegador nesta tela.

## Criar evento ou reunião

Linha de data: `[data inicial] [hora inicial] até [hora final] [data final]` e a chave **Dia inteiro**.

| Caso | Como preencher | No calendário |
|---|---|---|
| Compromisso no dia | data, hora inicial e hora final | bloco no horário |
| Período com horário (ex.: viagem sexta 14h até segunda 8h) | data e hora de início, data e hora de fim | barra cobrindo os dias |
| Dia inteiro / vários dias (ex.: férias, atestado) | marcar **Dia inteiro**, dia inicial e dia final | barra pintando todos os dias |

Sem limite de duração. Ao mudar o início, o fim acompanha mantendo a duração. O rótulo mostra "Duração: 3 h 30 min" ou "15 dias".

Barras de vários dias ficam no topo do dia e empurram os demais eventos para baixo, sem sobrepor.

Validação (front e `_dados_formulario`): fim depois do início; em dia inteiro, data final igual ou depois da inicial. Em dia inteiro, o FullCalendar trata o `end` como exclusivo (o JS soma/subtrai 1 dia).

Reunião: participantes, disponibilidade de cada um e **Sugerir horários livres** (`/agenda/sugerir`, duração de 15 min a 8 h, passos de 30 min no expediente).

### Reunião intersetorial

- A lista já vem com as pessoas das suas unidades. Para chamar alguém de **outro setor**, digite o nome (2 letras ou mais): o campo busca na rede toda em `GET /agenda/pessoas?q=` (sem acento, até 20 resultados) e mostra o setor embaixo do nome.
- O servidor aceita qualquer usuário ativo como participante (`_ids_participantes_form`).
- A reunião aparece na agenda de cada participante, seja qual for a unidade dele.
- **Privacidade:** na disponibilidade, um compromisso que você não enxergaria na sua agenda (de outro setor ou pessoal) aparece só como "Ocupado", sem o título.

## Ausência / férias

Terceiro tipo no modal (aba **Ausência**, ícone de guarda-sol). Serve para a unidade inteira ver quem está fora e ninguém marcar reunião com essa pessoa.

- Campos: **quem estará fora** (só você mesmo, ou qualquer pessoa da unidade se tiver `editar_agenda`), **motivo** e o período (já abre em "Dia inteiro"). Título e local são gerados: "Férias: Nome Sobrenome" ou "Ausente: Nome Sobrenome".
- Motivos (`motivos_ausencia_agrupados` em `app/models/frequencia.py`): afastamentos da coluna Complemento da planilha do RH (férias, licença-prêmio, maternidade…), as siglas da aba Instruções (FA, AM, DCM, LN…) e "Outro motivo".
- Visibilidade sempre **unidade**, cor cinza (`COR_AUSENCIA`). Coluna `agenda_eventos.motivo` (`migrations/add_agenda_ausencia.py`).
- **Privacidade do motivo:** só vê o motivo quem criou, quem está ausente e quem tem `editar_agenda`. Os demais veem só "Férias" ou "Ausente".
- Na disponibilidade da reunião, a pessoa aparece como fora (guarda-sol, `fora: true`), e conta como ocupada só para ela, não para quem registrou.
- A pessoa ausente também pode editar e excluir o registro.
- É manual: importar a planilha de frequência **não** cria ausências na agenda.

## Veículos

Quarto tipo no modal (aba **Veículo**, aparece se o usuário tem veículo em alguma das suas unidades). Acaba com a dúvida "quem pegou o carro".

- Veículo tem cadastro próprio, sem ligação com equipamentos: tabela `veiculos` (`app/models/veiculo.py`), ligada só à unidade. Formulário em `/veiculos/novo/<unidade_id>` e `/veiculos/<id>/editar` (permissões `cadastrar_veiculo` / `editar_veiculo`, seção **Veículos** em Perfis). Desativar/reativar fica na página do veículo; reserva antiga continua no histórico.
- A identificação é o **prefixo** (ex.: 383); com o check "Alugado" ele aparece como **AL-383** (`Veiculo.prefixo_exibicao`, usado no rótulo da agenda, nos cartões e no RDV). Digitar "AL-383" no prefixo marca Alugado sozinho. Placa é única entre os ativos, e o par prefixo + alugado também.
- Marca e modelo são texto livre com sugestões do catálogo `veiculo_modelos` (modelos populares brasileiros com categoria, semeados por `migrations/add_veiculos_reservas.py`); escolher o modelo preenche marca e categoria.
- Quem reserva: qualquer pessoa vinculada à unidade do carro. Campos: veículo, **quem vai usar** (`condutor_id`, padrão = quem registra), destino e período. Título automático "Prefixo · Placa · Marca Modelo → destino".
- Conflito: dois usos do mesmo veículo no mesmo horário são recusados (409) em criar, editar e arrastar. Ao escolher veículo e horário, o modal já avisa se está livre (`POST /agenda/veiculo-livre`).
- Na leitura aparecem **quem registrou e quando**, quem vai usar e o km. Km de saída e de chegada são preenchidos na volta (`POST /agenda/eventos/<id>/km`) por quem registrou, pelo condutor ou por quem pode editar o evento; chegada menor que saída é recusada.
- Cor `COR_VEICULO` e filtro **Veículos** na barra lateral.
- Aba **Veículos** no detalhe da unidade: cartões com placa, km atual (último km de chegada ou o do cadastro), em uso / próxima reserva, usos sem km e atalhos para reservar, usos, RDV e editar.
- `/veiculos/<id>` (`app/routes/veiculos.py`): usos do mês com km editável e **RDV** (`/veiculos/<id>/rdv?mes=AAAA-MM`), planilha Excel com um uso por linha (data, condutor, destino, horários, km, km rodados por fórmula, assinatura). O layout é provisório até chegar o modelo oficial.

## Salas de reunião e auditórios

- Tipo de sala com **Reservável na agenda** (`tipos_sala.reservavel`; Sala de Reunião AMB-41 e Auditório já marcados). Na sala desse tipo aparece **Disponível para todas as unidades** (`salas.uso_compartilhado`).
- Em evento ou reunião, depois de data e hora, o botão **Verificar salas vazias** (`POST /agenda/salas-livres`) lista, nesta ordem: salas da unidade do evento, salas compartilhadas do **mesmo prédio/endereço** (`predio_id`, senão endereço + número normalizados) e as compartilhadas do resto da rede. Salas ocupadas aparecem com quem reservou.
- Escolher a sala grava `agenda_eventos.sala_id` e preenche o local. Reserva no mesmo horário é recusada (409); sala privada de outra unidade, 400.
- A unidade dona da sala também enxerga as reservas dela na agenda.
- A capacidade mostrada ("até N pessoas") vem do campo "Máx. profissionais simultâneos" da sala.

Lógica em `app/services/reservas.py` (conflitos, salas livres, situação e km dos veículos).

## Arrastar (drag & drop)

| O que | Como | Rota |
|---|---|---|
| Mudar o dia | arrastar no mês | `POST /agenda/eventos/<id>/mover` |
| Mudar o horário | arrastar na semana/dia (encaixe de 15 min) | idem |
| Mudar a duração | esticar a borda do evento | idem |

- Só arrasta quem pode editar o evento (`_pode_editar_evento` → `editable` no JSON). Feriados não arrastam.
- Depois de soltar aparece o aviso "Evento movido…" / "Reunião movida…" / "Horário ajustado…" com **Desfazer** por 7 s.
- Se o servidor recusar, o evento volta para o lugar.

## Prazos das ações

Antes o prazo, uma vez definido, não podia ser alterado. Agora pode ser **definido, alterado ou removido**, e toda mudança entra no histórico da ação.

### Por onde

- **Agenda:** arrastar o prazo para outro dia (só na faixa de dia inteiro) abre o modal "Alterar prazo" com a data nova e o motivo (opcional). **Cancelar** devolve o prazo ao dia original. Também dá para clicar no prazo e usar o lápis **Alterar prazo**.
- **Planejamentos:** lápis ao lado do prazo em todas as ações (com ou sem prazo). Modal com data, motivo e **Remover prazo**.

### Regras

- Quem pode: `pode('criar_acao')` **e** acesso ao planejamento (`_usuario_pode_editar_planejamento`). Na agenda, o prazo só fica arrastável nesses casos e se a ação não estiver concluída.
- `POST /planejamentos/acoes/<id>/prazo` com `prazo` (`AAAA-MM-DD`; vazio = remover), `motivo` e `origem` (`agenda` ou `planejamento`). Responde `ok`, `mudou`, `prazo`, `prazo_iso`, `prazo_dias_texto`, `atualizado_em`.
- `alterar_prazo_acao` grava uma `AcaoObservacao` com autor e data:
  - "Prazo definido para **05/11/2026**."
  - "Prazo alterado de **21/10/2026** para **23/10/2026** pela agenda."
  - "Prazo removido (era **30/10/2026**)."
  - "**Motivo:** …" quando informado (texto escapado).
- Atualiza `atualizado_em/por` da ação e do planejamento.
- Cada responsável da ação (menos quem alterou) recebe a notificação `prazo_alterado` ("Prazo de ação alterado").

Sem migration: usa colunas e tabelas que já existiam (`acoes_planejamento.prazo`, `acoes_planejamento_observacoes`, `notificacoes`).

## Armadilhas já resolvidas

- `sigus.js` fecha sozinho todo `.alert` depois de 5 s. Alerta usado por JS precisa de `alert-permanent`, senão o elemento some e o modal quebra (era o bug "evento não abre").
- Ao mexer no CSS da agenda, aumente o `?v=` do link de `agenda.css` no template.
