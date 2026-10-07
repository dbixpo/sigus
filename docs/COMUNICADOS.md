# Comunicados e ciência

Módulo do dashboard: recado oficial da unidade (ou da Secretaria, quando o gestor central compartilha), com trilha de ciência.

Código: `app/routes/noticias.py`, `app/models/noticias.py`, templates em `app/templates/noticias/`.

## Quem publica

Perfis em `PERFIS_PUBLICAR`: apoio administrativo, coordenador, gestor central, administrador. Quem só opera a unidade lê e assina; não cria comunicado.

Gestor central e administrador escolhem as unidades. Os demais publicam só na unidade do seletor do topo.

## Ordem do formulário

1. Título
2. Texto
3. Documento para anexar (opcional, até 5 arquivos)
4. Unidade(s)
5. Cobrar ciência
6. Quem deve dar ciência (só se o passo 5 estiver marcado)
7. Publicar

## Recorte da ciência (perfil **ou** CBO)

Não é AND. Quem publica escolhe **um** modo:

| Modo | O que grava | Quem entra |
|---|---|---|
| Toda a equipe (padrão) | `ciencia_perfis` e `ciencia_cbos` vazios | Vínculo ativo nas unidades do recado |
| Por perfil | JSON de perfis SIGUS | Mesmo vínculo **e** perfil marcado |
| Por CBO | JSON de códigos CBO | Mesmo vínculo **e** CBO no **cadastro** da pessoa **ou** em **matrícula ativa** |

A ocupação da ficha CNES da unidade (ex.: gestor 131210) **não** entra na lista nem no matching. Por isso a enfermeira cujo CBO profissional está na matrícula aparece em enfermagem, mesmo com ficha de gestora na unidade.

Se um comunicado antigo tiver os dois JSON preenchidos, o matching passa a ser **OU** (perfil ou CBO).

Autor **não** ganha ciência automática. Se ele também for destinatário, o sistema o leva para assinar.

## Chave "Ver todos" no card do dashboard

Por padrão o card esconde os comunicados em que o usuário já deu ciência (classe `com-lido`): fica só o que falta assinar e os informativos sem cobrança de ciência. Ligando a chave **Ver todos** no cabeçalho, os já assinados voltam. A escolha fica salva no navegador (`localStorage`, chave `sigus.dash.comunicados.todos`). Se tudo estiver assinado, aparece "Tudo em dia" com um atalho "Ver N já lidos". Como a ciência é por versão, um comunicado editado volta a aparecer sozinho.

## Editar e excluir (comunicados e mural)

Os botões ficam no próprio card do dashboard e na página do comunicado. Os botões soltos "Novo comunicado" e "Registrar ação" no topo do dashboard saíram: o card já tem o seu.

| Ação | Quem pode | Função |
|---|---|---|
| Editar | só quem publicou | `_pode_editar` |
| Excluir | quem publicou **ou** perfil `administrador` | `_pode_excluir` |

Vale igual para comunicado (`/comunicados/<id>/editar`, `/comunicados/<id>/excluir`) e para postagem do mural de ações (`/mural/acoes/<id>/editar`, `/mural/acoes/<id>/excluir`).

**Comunicado editado pede ciência de novo.** Cada edição que muda algo sobe `versao`. A ciência é contada por versão (`ComunicadoCiencia.versao`), então as assinaturas da versão anterior deixam de valer e os destinatários são notificados de novo. As assinaturas antigas continuam no banco como histórico. Se nada mudou, o sistema avisa "Nada foi alterado" e não zera nada.

Exclusão de comunicado é lógica (`ativo = False`, `excluido_em`, `excluido_por_id`). Exclusão de postagem do mural apaga a ação e as fotos.

**Texto do mural:** as quebras de linha aparecem também no card fechado, não só ao expandir.

## Banco

Colunas TEXT na tabela `comunicados` (JSON de listas):

```
migrations/add_ciencia_filtros.py
```

Idempotente. Sem coluna nova para o “modo”: listas vazias = toda a equipe.

Versão, edição e exclusão:

```
migrations/add_comunicado_versao.py
```

Idempotente. Adiciona `versao`, `editado_em`/`editado_por_id`, `excluido_em`/`excluido_por_id` em `comunicados`, `versao` na ciência e a restrição única `(comunicado_id, usuario_id, versao)`.

## Conferência

- `/sigus/comunicados/novo` com a unidade Saúde Digital (ou a que tiver Lina/Camila): modo **Por CBO** deve listar enfermagem (223505) e fisioterapia (223605), não só o CBO de quem preencheu o cadastro SIGUS.
- AJAX: `/sigus/comunicados/opcoes-ciencia?unidades=<id>`
