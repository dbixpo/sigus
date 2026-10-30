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

## Quem pode cadastrar qual perfil

No cadastro e na edição de usuário (`/usuarios/novo` e `/usuarios/<id>/editar`), o perfil que pode ser gravado segue esta tabela. Quem edita uma pessoa cujo perfil está fora da lista vê o perfil travado e o servidor recusa a troca.

| Quem cadastra | Administrador | Gestor Central | Gestor de Área | Apoio Administrativo | Operador Padrão |
|---|---|---|---|---|---|
| Administrador | sim | sim | sim | sim | sim |
| Gestor Central | não | não | sim | sim | sim |
| Gestor de Área | não | não | não | sim | sim |
| Apoio Administrativo | não | não | não | não | sim |
| Operador Padrão | não | não | não | não | não |

Operador Padrão também não abre a tela de usuários. A lista fica em `_PERFIS_PERMITIDOS` (`app/routes/usuarios.py`).

## Testar o sistema como outro perfil

Quem está gravado como **Administrador** pode, no menu do próprio nome, escolher outro perfil. A troca vale só naquela sessão: menus, botões e bloqueios passam a ser os daquele perfil. O cadastro não muda. A faixa amarela **Voltar ao Administrador** desfaz a simulação, inclusive se o perfil testado não tiver acesso às configurações. Sair do sistema também desfaz.

## Matriz de seções

Em **Configurações → Gestão de Perfis** cada perfil (exceto Administrador) ganha Ver / Editar / Adicionar. A lista está em `SECOES` (`app/models/perfil_permissao.py`). Se a linha existe, vale o que está gravado: desmarcar o Ver de um item filho fecha aquele item mesmo com o grupo pai ligado. A herança do Ver do pai só existe enquanto a linha daquele item nunca foi salva.

| Grupo | O que o interruptor controla |
|---|---|
| Patrimônio | Prédios, unidades, salas, equipamentos e a aba de veículos da unidade |
| Operações | Chamados, gestão de chamados, transferências, contratos, emendas, licitações, chamados SUEQ, controle de empenho, empresas |
| Gestão | Agenda, planejamentos, Segurança do Paciente (menu), relatórios, mural e comunicados |
| Outros | Links úteis, o link/QR do cadastro público e Metabase (`OUT_Metabase`) |
| Recursos humanos | Faltas abonadas e apontamentos da unidade (planilha do RH) |
| Configurações | Cada catálogo separado: feriados, tipos de ação, tipos de unidade, padrão e tipos de sala, classificação RENEM, catálogo e status de equipamento, catálogo de veículos, marcas e modelos, divisões, status de chamados, CBOs, catálogos da Segurança do Paciente, identidade, usuários e auditoria |

Como ler os três interruptores quando o rótulo não é óbvio:

- **Mural:** Ver mostra o mural. Adicionar publica na própria unidade. Editar comunica para várias unidades.
- **Apontamentos da unidade:** a tela só abre para Gestor de Área, Gestor Central e Administrador. Dá para trocar a unidade do alcance de cada um, mas a lista mostra só a planilha que a própria pessoa importou. Quem não subiu arquivo não vê lançamento nenhum. “Meus apontamentos” continua pessoal.
- **Relatórios:** um interruptor para todos os relatórios do menu.
- **Identidade e assets:** município, logos e domínio de e-mail. O Administrador sempre entra; os demais só com esta linha marcada.
- **Gestão de Perfis:** só o Administrador. A linha da matriz não abre essa tela para outro perfil.
- **Segurança do Paciente:** Ver abre o menu. Quem conduz os casos continua sendo a lista de membros do Núcleo e das comissões, não o perfil.
- **Metabase:** Ver abre o menu e os painéis liberados para o perfil, o tipo da unidade e o CBO. Editar e Adicionar abrem Configurações → Metabase. Na matriz nova, isso fica com o Gestor Central; o Administrador entra sempre. Detalhe: [METABASE.md](METABASE.md).
- **Equipamentos na unidade:** incluir e corrigir cadastro seguem Adicionar e Editar. Depois do primeiro inventário, a unidade continua podendo transferir e mudar o estado do bem.

O script `migrations/seed_permissoes_faltantes.py` só cria a linha que ainda não existe, com o mesmo acesso que a pessoa já tinha. Não regrava o que já foi salvo.

## Vínculo com unidade

Perfis da ponta **exigem** pelo menos uma unidade ativa. Sem vínculo, o sistema manda para a tela de “sem vínculo”. Administrador / gestor central circulam na rede, mas **ações no nome de uma unidade** (finalizar Lojinha) usam o seletor do topo (`unidade_padrao_id`). Exceção: no termo de transferência (`/transferencias/novo` e o aceite) esses dois perfis operam qualquer origem/destino, para realocar inventário entre unidades.

`Usuario.ids_unidades_efetivos()`:

- Sem vínculo → `None` (em vários fluxos isso bloqueia a ação com flash “selecione uma unidade”)
- Com unidade padrão válida → só essa unidade
- Senão → todas as vinculadas

Pedido novo: formulário público `/solicitar-vinculo-profissional`. A coordenação aprova na ficha da unidade.

## Gestão de chamados

Além da permissão `OP_GestaoChamados`, a pessoa precisa estar vinculada a um **setor de manutenção** (`UsuarioSetor`). Unidade prestadora do tipo de chamado se configura no cadastro da unidade (`unidade_tipos_chamado_recebe`). Se o chamado “não aparece na fila”, em geral falta essa marcação — não é bug da lista.

## Segurança do Paciente

Aqui o perfil **não** decide quem vê os casos. Vale a lista de membros (`nsp_membros`), em **Configurações → Segurança do Paciente**:

- **Núcleo**: vê e conduz todos os casos.
- **Comissão** de uma unidade: vê os casos encaminhados a ela.
- **Coordenação** (gestor principal/secundário ou Gestor de Área vinculado): só os casos que o Núcleo liberar.

Administrador e Gestor Central não veem casos se não estiverem na lista. Notificar é livre para todos, inclusive sem login. Detalhes em [SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md).

## Telas públicas com QR code

Links Úteis, Cadastro Público, notificação de Segurança do Paciente e Mapa da Saúde têm versão aberta, sem login. A versão interna mostra os botões **Acesso público**, **QR code** e **copiar endereço**. Ver [MAPA_DO_CODIGO.md](MAPA_DO_CODIGO.md#telas-públicas-sem-login).

## Regras práticas

- Login é pessoal. Auditoria grava usuário, IP e endpoint ([05_AUDITORIA.md](05_AUDITORIA.md)), exceto na notificação de Segurança do Paciente, que é anônima.
- Não compartilhe senha de administrador para “ver o menu do colega”: use um usuário de teste com o perfil certo.
- Reset de senha: `scripts/reset_usuario_sigus.py`. **Nunca** rode `migrations/recriar_admin.py` em produção — ele **apaga todos** os administradores e recria um.
