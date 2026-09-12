# Permissões, perfis e unidade de trabalho

O menu e os botões **não são fixos**. O que a pessoa vê depende de três coisas ao mesmo tempo:

1. **Perfil** (`usuarios.perfil`)
2. **Matriz Ver / Editar / Adicionar** em `perfil_permissoes` (tela Configurações → Gestão de Perfis)
3. **Vínculo com unidade** (`usuario_unidade`) e, para a fila de chamados, **setor de manutenção**

No código: `current_user.pode('abrir_chamado')` etc. (`Usuario.pode` em `app/models/usuario.py`). Mapeamento ação → seção: `ACAO_PARA_SECAO_TIPO` em `app/models/perfil_permissao.py`.

## Perfis (`PERFIS`)

| Chave no banco | Rótulo na tela | Papel típico |
|---|---|---|
| `administrador` | Administrador | Tudo. `pode()` retorna True sem consultar a matriz. Só este perfil gerencia perfis. |
| `gestor_secretaria` | Gestor Central | Rede, relatórios, contratos |
| `coordenador` | Gestor de Área | Unidades vinculadas, planejamentos |
| `administrativo` | Apoio Administrativo | Cadastros da unidade, patrimônio, chamados |
| `profissional` | Operador Padrão | Rotina: chamado, NSP, falta abonada, agenda |

Hierarquia numérica (não substitui a matriz): administrador 5 … profissional 1.

## Matriz de seções

Em **Configurações → Gestão de Perfis** cada perfil ganha Ver / Editar / Adicionar por seção (`SECOES`): patrimônio (prédios, unidades, salas, equipamentos), operações (chamados, gestão, transferências, contratos, emendas, licitações, SUEQ, empenho, empresas), gestão (planejamentos, agenda, Segurança do Paciente, relatórios), RH, links, cadastro público, configurações, usuários, auditoria.

- Item **desmarcado** some do menu daquele perfil.
- Administrador não precisa dessa tela para si; ela vale para os outros.
- Não “teste” permissão no perfil de toda a rede em produção.

## Vínculo com unidade

Perfis da ponta **exigem** pelo menos uma unidade ativa. Sem vínculo, o sistema manda para a tela de “sem vínculo”. Administrador / gestor central circulam na rede, mas **ações no nome de uma unidade** (aceite de termo, finalizar Lojinha, abrir NSP) usam o seletor do topo (`unidade_padrao_id`).

`Usuario.ids_unidades_efetivos()`:

- Sem vínculo → `None` (em vários fluxos isso bloqueia a ação com flash “selecione uma unidade”)
- Com unidade padrão válida → só essa unidade
- Senão → todas as vinculadas

Pedido novo: formulário público `/solicitar-vinculo-profissional`. A coordenação aprova na ficha da unidade.

## Gestão de chamados

Além da permissão `OP_GestaoChamados`, a pessoa precisa estar vinculada a um **setor de manutenção** (`UsuarioSetor`). Unidade prestadora do tipo de chamado se configura no cadastro da unidade (`unidade_tipos_chamado_recebe`). Se o chamado “não aparece na fila”, em geral falta essa marcação — não é bug da lista.

## Regras práticas

- Login é pessoal. Auditoria grava usuário, IP e endpoint ([05_AUDITORIA.md](05_AUDITORIA.md)).
- Não compartilhe senha de administrador para “ver o menu do colega”: use um usuário de teste com o perfil certo.
- Reset de senha: `scripts/reset_usuario_sigus.py`. **Nunca** rode `migrations/recriar_admin.py` em produção — ele **apaga todos** os administradores e recria um.
