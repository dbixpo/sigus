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

Validação (front e `_dados_formulario`): fim depois do início; em dia inteiro, data final igual ou depois da inicial. Em dia inteiro, o FullCalendar trata o `end` como exclusivo (o JS soma/subtrai 1 dia).

Reunião: participantes, disponibilidade de cada um e **Sugerir horários livres** (`/agenda/sugerir`, duração de 15 min a 8 h, passos de 30 min no expediente).

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
