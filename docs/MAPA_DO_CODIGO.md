# Mapa do código — blueprints e rotas

Todas as URLs abaixo são relativas ao prefixo `/sigus`. Exemplo: blueprint `/login` = `https://…/sigus/login`.

Registro: `app/__init__.py` (`create_app`).

| Blueprint | Prefixo | Arquivo | Para que serve |
|---|---|---|---|
| `auth` | `/` | `app/routes/auth.py` | Login, logout, perfil, unidade padrão |
| `dashboard` | `/` | `app/routes/dashboard.py` | Home após o login |
| `noticias` | `/` | `app/routes/noticias.py` | Comunicados, ciência, mural de ações |
| `unidades` | `/configuracoes/unidades` | `app/routes/unidades.py` | Ficha da unidade (abas: salas, equipamentos, NSP, profissionais…) |
| `predios` | `/configuracoes/predios` | `app/routes/predios.py` | Prédios |
| `salas` | `/salas` | `app/routes/salas.py` | CRUD de sala + **cadastro externo** |
| `equipamentos` | `/equipamentos` | `app/routes/equipamentos.py` | Inventário, ficha, baixa, usuários do bem |
| `chamados` | `/chamados` | `app/routes/chamados.py` | Abrir / acompanhar / gestão (fila) |
| `chamados_externo` | `/abrir-chamado` | `app/routes/chamados_externo.py` | Chamado **público** (sem login) |
| `transferencias` | `/transferencias` | `app/routes/transferencias.py` | Termos, aceite, Lojinha |
| `contratos` | `/contratos` | `app/routes/contratos.py` | Contratos |
| `contrato_financeiro` | `/contratos/empenhos` | `app/routes/contrato_financeiro.py` | Empenhos |
| `empresas` | `/empresas` | `app/routes/empresas.py` | Empresas contratadas |
| `sueq` | `/sueq` | `app/routes/sueq.py` | Emendas / licitações / chamados SUEQ (schema `sueq`) |
| `planejamentos` | `/planejamentos` | `app/routes/planejamentos.py` | Planos GUT / Kanban; prazo editável com histórico (`alterar_prazo_acao`) |
| `agenda` | `/agenda` | `app/routes/agenda.py` | Agenda estilo Google + reuniões; arrastar (`/eventos/<id>/mover`). Ver [AGENDA_E_PLANEJAMENTOS.md](AGENDA_E_PLANEJAMENTOS.md) |
| `nsp` | `/seguranca-paciente` | `app/routes/nsp.py` | Segurança do Paciente no fluxo do Núcleo (notificação pública, qualificação, comissões, relatórios). Ver [SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md) |
| `relatorios` | `/relatorios` | `app/routes/relatorios.py` | Inventário, salas, NSP, mapa, aniversariantes… |
| `rh` | `/rh` | `app/routes/rh.py` | Faltas abonadas |
| `frequencia` | `/rh` | `app/routes/frequencia.py` | Importar planilha de frequência, Meus apontamentos, apontamentos da unidade, base de servidores, locais do RH. Ver [FREQUENCIA_RH.md](FREQUENCIA_RH.md) |
| `solicitacoes` | `/solicitar-vinculo-profissional` | `app/routes/solicitacoes.py` | Cadastro público de vínculo |
| `usuarios` | `/usuarios` | `app/routes/usuarios.py` | Usuários (quem tem permissão) |
| `configuracoes` | `/configuracoes` | `app/routes/configuracoes.py` | Tipos (sala com kit padrão, equipamento com catálogo ITEM), marcas, perfis, feriados, CBOs e funções do RH × CBO, catálogos NSP, auditoria |
| `links` | `/links` | `app/routes/links.py` | Links úteis: `/links` é interno para quem está logado e público para quem não está; `/links/publico` é sempre público; administração; QR code por link |
| `notificacoes` | `/notificacoes` | `app/routes/notificacoes.py` | Sino (JSON) |

Redirects legados (continuam funcionando): `/unidades` → `/configuracoes/unidades`, `/predios` → `/configuracoes/predios`, URLs antigas do mapa → `/mapa-da-saude`.

## Telas públicas (sem login)

Trate como superfície de internet: CSRF, validação, sem dado clínico.

| URL | Uso |
|---|---|
| `/login` | Entrada |
| `/abrir-chamado` | Chamado externo |
| `/solicitar-vinculo-profissional` | Pedido de vínculo (coordenação aprova na ficha da unidade) |
| `/salas/cadastro-externo` | Mutirão de salas |
| `/mapa-da-saude` | Mapa público da rede |
| `/links` (sem login) e `/links/publico` | Links Úteis liberados para todos os perfis. O endereço curto `/sigus/links` é o que vai no QR e no copiar |
| `/seguranca-paciente/notificar` | Notificação de incidente (anônima por padrão) |
| `/seguranca-paciente/notificado/<protocolo>` e `/seguranca-paciente/acompanhar` | Comprovante e consulta da etapa pelo protocolo |

Endpoints livres de vínculo com unidade (abrem mesmo para usuário logado sem vínculo): `_ENDPOINTS_LIVRES` em `app/__init__.py`. Ao criar uma tela pública nova, inclua o endpoint ali.

### Acesso público e QR code

Padrão para divulgar uma tela pública. Na versão interna, um grupo de três botões: **Acesso público** (abre a página), **QR code** (baixa um PNG) e **copiar endereço**.

- O endereço vem de `url_publica('endpoint')` (context processor em `app/__init__.py`): usa `SIGUS_HOST_PUBLICO` do `.env`, para o QR nunca sair com `127.0.0.1` ou `localhost`.
- Script: `app/static/js/acesso-publico.js`, carregado no `base.html` com `qrcode.min.js`. Botões com `.js-qr-baixar` (`data-url`, `data-titulo`, `data-arquivo` opcional) e `.js-copiar-url` (`data-url`). Também expõe `window.SigusAcessoPublico`.
- O cartão PNG segue a identidade visual: faixa vermelha/amarela/azul, título (quebra em até 2 linhas, ou no ` · `), QR em `#0D3B5E`, endereço quebrado nas barras e rodapé "SIGUS · Saúde Digital". Endereço relativo vira absoluto; sem `data-arquivo`, o nome do arquivo sai do título.
- Modal com prévia do QR: `.js-acesso-publico` abre `#modalAcessoPublico` (no `base.html`), usado em Cadastro Público e Segurança do Paciente.
- Ao mudar o script, aumente o `?v=` no `base.html` e em `links/publico.html`.

Onde já está: Links Úteis (cabeçalho e cada link), Cadastro Público (menu), Segurança do Paciente (início e painel) e Mapa da Saúde (relatório interno).

## Models

Pasta `app/models/`. Os mais centrais:

| Módulo | Arquivo |
|---|---|
| Usuário, perfil | `usuario.py` |
| Unidade, vínculo | `unidade.py` |
| Sala | `sala.py` |
| Tipo de sala, kit padrão | `tipo_sala.py` (`TipoSala`, `KitPadraoSala`); conta em `app/services/padrao_salas.py` |
| Equipamento | `equipamento.py` |
| Chamado | `chamado.py` |
| Transferência / lojinha | `transferencia.py` |
| NSP | `nsp.py` |
| Permissões | `perfil_permissao.py` |
| Auditoria | `auditoria.py` |
| SUEQ | `sueq.py` (tabelas no schema PostgreSQL `sueq`) |

## Front-end

- CSS/JS globais: `app/static/css/`, `app/static/js/sigus.js`
- Logos: `app/static/img/logo-sd-branco.png` (fundo escuro), `logo-sd-colorido.png` (fundo claro)
- Impressos: modal padrão `abrirImpresso(…)` no `base.html` (chamado, termo, NSP, falta abonada)

## Onde **não** procurar bug do SIGUS

`app/static/references/samu/` é material de referência de outro sistema. Não está registrado em `create_app`.
