# Padrão de salas e equipamentos

Origem: planilha do Planejamento com o padrão de ambientes das UBS, o catálogo de itens e o kit de cada ambiente. O SIGUS adotou os códigos da planilha (`AMB-xx` para ambientes, `ITEM-xxx` para itens), para a planilha e o sistema falarem a mesma língua.

## Conceitos

| Na planilha | No SIGUS | Onde |
|---|---|---|
| Ambiente padrão (`AMB-01`…) | Tipo de sala **com código** | `tipos_sala.codigo`, `grupo`, `ordem` |
| Item (`ITEM-001`…) | Tipo de equipamento **com código** | `tipos_equipamento.codigo`, `classificacao`, `valor_referencia`, `natureza_kit` |
| Kit do ambiente | Kit padrão do tipo de sala | tabela `kit_padrao_sala` (tipo de sala × tipo de equipamento × quantidade) |
| Código do imóvel | Código do imóvel da unidade | `unidades.codigo_imovel` |

- **Tipo de sala sem código** continua valendo para o cadastro de salas, mas fica fora da conta do padrão. Ex.: "Consultório" genérico, Laboratório, Expurgo. As salas desses tipos aparecem como **a reclassificar**.
- **Tipo de equipamento sem código** (Monitor, Impressora, Tablet, Ar-condicionado…) continua no inventário e não entra em kit.
- **Natureza** (regra do Planejamento): **Base** pertence à sala física e conta uma vez por sala. **Função** pertence ao serviço. O compartilhamento de função entre salas ainda não é calculado; hoje cada sala é avaliada pelo kit do seu próprio tipo.
- **Conta como** (`tipos_equipamento.conta_como_id`): um tipo que atende a outro item do catálogo. Ex.: "Computador All-In-One" conta como `ITEM-051` Computador (Gabinete). Os tipos que já existiam mantiveram o nome, porque `transferencias._inferir_tipo_equipamento_id` procura por nome.

## Conta da aderência

`app/services/padrao_salas.py`:

- `calcular_aderencia(unidade_ids, tipo_unidade_ids, tipo_sala_ids, so_unidades_do_padrao)` avalia as salas ativas de unidades ativas.
- `aderencia_sala(sala)` alimenta a aba **Padrão do ambiente** no detalhe da sala.
- Encontrado = equipamentos `ativo=True` e `status != 'baixado'` da sala, agrupados por tipo, já aplicando o "conta como".
- Para cada item do kit: falta = max(0, esperado − encontrado), sobra = max(0, encontrado − esperado), custo = falta × valor de referência.
- Aderência = Σ min(encontrado, esperado) ÷ Σ esperado.
- Situação da sala: **avaliada** (ambiente com kit), **sem kit** (ambiente com código, kit vazio) ou **sem padrão** (tipo sem código).

Enquanto mobiliário e equipamentos médicos não forem inventariados no SIGUS, eles aparecem como faltando. O número de aderência sobe à medida que o inventário é completado.

## Telas

| Tela | Rota | Quem |
|---|---|---|
| **Hub do padrão** (menu Configurações → Padrão de Salas): números do padrão, atalhos e a lista "ligar inventário ao catálogo" | `/configuracoes/padrao-salas` | Configurações |
| **Encaixar salas existentes**: reclassifica em lote as salas de tipos sem código para um ambiente AMB, com sugestão pelo nome (`sugerir_ambiente` em `app/services/padrao_salas.py`) | `/configuracoes/padrao-salas/reclassificar` | Configurações + `editar_sala` |
| Tipos de sala agrupados pelo catálogo, com contagem de salas e itens do kit | `/configuracoes/tipos-sala` | Configurações |
| Editar tipo de sala: código, grupo, ordem e o **kit** (adicionar, mudar quantidade, remover) | `/configuracoes/tipos-sala/<id>/editar` | Configurações |
| Tipos de equipamento agrupados por classificação, com código, valor, natureza e "conta como" | `/configuracoes/tipos-equipamento` | Configurações |
| Relatório de aderência (por unidade, necessidade de compra por item, sala a sala, a reclassificar) e Excel | `/relatorios/padrao-salas` | `emitir_relatorios` |
| Aba **Padrão do ambiente** no detalhe da sala | `/salas/<id>` | quem vê a sala |

Os dados que já existiam antes do padrão continuam valendo e entram na conta de dois jeitos:

- **Salas**: as de tipo genérico (ex.: "Consultório") ficam "a reclassificar" até alguém escolher o ambiente na tela Encaixar salas existentes. A sugestão só é gravada se a linha estiver marcada; a sala muda de tipo, os equipamentos não mudam.
- **Equipamentos**: um tipo do inventário que não é item do catálogo (ex.: "Computador All-In-One") passa a contar quando é ligado a um item ("conta como" ITEM-051). Tipos sem item correspondente (Monitor, Impressora) ficam fora do padrão.

O relatório abre, por padrão, só nas **UBS do padrão** (unidades com código de imóvel, que vieram da planilha). "Todas as unidades" no filtro Abrangência inclui as demais. O detalhe sala a sala aparece com até 5 unidades no filtro; o Excel traz todas.

Os selects de tipo de sala (cadastro de sala e cadastro externo) e de tipo de equipamento aparecem agrupados (filtros `agrupar_tipos_sala` e `agrupar_tipos_equipamento` em `app/utils.py`).

## Importação da planilha

```powershell
.\venv\Scripts\python.exe migrations\add_padrao_salas.py
.\venv\Scripts\python.exe migrations\importar_padrao_salas.py              # simulação, desfaz no fim
.\venv\Scripts\python.exe migrations\importar_padrao_salas.py --aplicar    # grava
.\venv\Scripts\python.exe migrations\importar_padrao_salas.py --pendencias C:\caminho\Pendencias.xlsx
```

- Lê `migrations/dados/padrao_salas_ubs.xlsx`, ou o arquivo indicado em `--planilha`. A planilha **não** vai para o Git (`migrations/dados/` está no `.gitignore`); peça o arquivo ao Planejamento. Abas usadas: Ambientes Padrão, Itens, Kit — Lista, Unidades.
- Idempotente: rodar de novo só atualiza.
- Ambientes: casa por código, depois pelo de-para `DE_PARA_SALAS` (tipos que já existiam no SIGUS), depois pelo mesmo nome. O tipo casado recebe o nome e o código da planilha.
- Itens: casa por código, depois `DE_PARA_ITENS`, depois mesmo nome. O tipo casado mantém o nome do SIGUS.
- Kit: soma as linhas repetidas do mesmo item no mesmo ambiente.
- Unidades: grava `codigo_imovel` casando pelo CNES. Com CNES repetido, prefere a unidade de Atenção Primária.
- `--pendencias` gera um Excel com o que a planilha precisa completar e as salas e equipamentos do SIGUS fora do padrão.

Depois que o catálogo estiver no SIGUS, a manutenção passa a ser pelas telas de configuração. Rodar a importação de novo sobrescreve nome, grupo, ordem e quantidades com o que estiver na planilha.
