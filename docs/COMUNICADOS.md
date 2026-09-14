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

## Banco

Colunas TEXT na tabela `comunicados` (JSON de listas):

```
migrations/add_ciencia_filtros.py
```

Idempotente. Sem coluna nova para o “modo”: listas vazias = toda a equipe.

## Conferência

- `/sigus/comunicados/novo` com a unidade Saúde Digital (ou a que tiver Lina/Camila): modo **Por CBO** deve listar enfermagem (223505) e fisioterapia (223605), não só o CBO de quem preencheu o cadastro SIGUS.
- AJAX: `/sigus/comunicados/opcoes-ciencia?unidades=<id>`
