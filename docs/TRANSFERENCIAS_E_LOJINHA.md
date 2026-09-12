# Transferências de equipamentos e Lojinha Interna

Código: `app/routes/transferencias.py`, `app/models/transferencia.py`.  
Telas: `app/templates/transferencias/`.  
Menu: **Operações → Transferências**.  
Manual da ponta: capítulo [Patrimônio…](https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sigus/chapter/patrimonio-salas-equipamentos-transferencias-e-lojinha) na Estante.

## Regra

Não apagar o bem numa unidade para cadastrar de novo em outra. O histórico mora no equipamento + nos documentos.

Há dois fluxos:

1. **Termo** (empréstimo, transferência ou doação) — lote ou um item.
2. **Solicitar** a partir da ficha do equipamento (`/transferencias/solicitar/<id>`).

A unidade de **destino** aceita em `/transferencias/documento/<id>/aceitar`, escolhe a **sala** e o SIGUS realoca (ou cadastra no inventário se o item veio “manual” com patrimônio). Recusa devolve o status sem mover.

Abas da lista: Pendentes de aceite | Enviadas | Concluídas | Lojinha Interna.

Classificação dos itens:

- **A** — inservível ao setor, plenas condições de uso
- **B** — inservível ao setor, usa mas precisa de reparo

Impresso: modal `abrirImpresso` (termo de transferência / doação). Documentos originados da Lojinha podem imprimir como **Termo de Doação**.

## Lojinha Interna

Tabela `itens_lojinha`. Vitrine por unidade. Carrinho no `localStorage` (`lojinha_cart`).

- Colocar à disposição: `/transferencias/lojinha/adicionar` (inventário ou item manual).
- Remover da vitrine: só a unidade dona.
- Finalizar: POST `/transferencias/lojinha/finalizar` — gera documento(s) para a **unidade padrão** do usuário. Não compra da própria unidade. Exige unidade selecionada no topo.
- Aceite posterior é o mesmo da aba Pendentes.

Migrations típicas: `add_documentos_transferencia.py`, `add_itens_lojinha.py`.
