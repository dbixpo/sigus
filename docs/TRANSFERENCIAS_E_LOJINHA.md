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

Em `/transferencias/novo`, administrador e gestor central escolhem **qualquer** unidade de origem e de destino (independente do seletor do topo) e veem o inventário das duas para realocar bens na atualização cadastral. Coordenador e administrativo continuam só com as unidades vinculadas. Os selects de unidade são pesquisáveis; ao escolher origem/destino o SIGUS lista os equipamentos ativos de cada uma. Depois de criar o termo, esses dois perfis caem direto na tela de aceite, escolhem a sala do prédio novo e concluem — a mesma pessoa cria e aceita.

A unidade de **destino** aceita em `/transferencias/documento/<id>/aceitar`, escolhe a **sala** e o SIGUS realoca (ou cadastra no inventário se o item veio “manual” com patrimônio). Recusa devolve o status sem mover. Coordenador/administrativo aceitam só quando a unidade do topo é a destino.

Abas da lista: Pendentes de aceite | Enviadas | Concluídas | Lojinha Interna.

Classificação dos itens:

- **A** — inservível ao setor, plenas condições de uso
- **B** — inservível ao setor, usa mas precisa de reparo

Impresso: modal `abrirImpresso` (termo de transferência / doação). Documentos originados da Lojinha podem imprimir como **Termo de Doação**.

## Veículos no termo

Em `/transferencias/novo`, o bloco **Veículos da origem** (`GET /transferencias/api/veiculos-unidade/<id>`) põe o carro no termo como item com `veiculo_id`. Carro de outra unidade, desativado, já em termo pendente ou emprestado não entra.

- **Transferência:** no aceite, `veiculos.unidade_id` passa para o destino (reservas e RDV seguem com a unidade nova).
- **Empréstimo:** pede **devolução prevista** (`documentos_transferencia.devolucao_prevista`). O carro continua da unidade dona; do aceite até alguém clicar em **Devolver** (`POST /transferencias/documento/<id>/devolver`, grava `devolvido_em` / `devolvido_por`) ele aparece também na agenda, na aba Veículos e na página `/veiculos/<id>` da unidade que pegou. Editar e desativar continuam só com a dona. O RDV é um só, o da dona, com os usos das duas.
- Termo só com veículo não pede sala no aceite. Termo misto pede sala só para os equipamentos.
- Aba Concluídas: "Emprestado até dd/mm" (vermelho se passou), "Devolvido em", botão Devolver e o filtro **Veículos emprestados agora**. A página do veículo mostra o mesmo aviso com o termo e o Devolver.
- Para uso de poucas horas por pessoa de outra unidade, não precisa termo: a própria agenda reserva para alguém de fora (ver `docs/AGENDA_E_PLANEJAMENTOS.md`).

Migração: `migrations/add_transferencia_veiculos.py`.

## Lojinha Interna

Tabela `itens_lojinha`. Vitrine por unidade. Carrinho no `localStorage` (`lojinha_cart`).

- Colocar à disposição: `/transferencias/lojinha/adicionar` (inventário ou item manual).
- Remover da vitrine: só a unidade dona.
- Finalizar: POST `/transferencias/lojinha/finalizar` — gera documento(s) para a **unidade padrão** do usuário. Não compra da própria unidade. Exige unidade selecionada no topo.
- Aceite posterior é o mesmo da aba Pendentes.

Migrations típicas: `add_documentos_transferencia.py`, `add_itens_lojinha.py`.
