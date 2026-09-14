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
| `planejamentos` | `/planejamentos` | `app/routes/planejamentos.py` | Planos GUT / Kanban |
| `agenda` | `/agenda` | `app/routes/agenda.py` | Agenda da unidade + reuniões |
| `nsp` | `/seguranca-paciente` | `app/routes/nsp.py` | Segurança do Paciente |
| `relatorios` | `/relatorios` | `app/routes/relatorios.py` | Inventário, salas, NSP, mapa, aniversariantes… |
| `rh` | `/rh` | `app/routes/rh.py` | Faltas abonadas |
| `solicitacoes` | `/solicitar-vinculo-profissional` | `app/routes/solicitacoes.py` | Cadastro público de vínculo |
| `usuarios` | `/usuarios` | `app/routes/usuarios.py` | Usuários (quem tem permissão) |
| `configuracoes` | `/configuracoes` | `app/routes/configuracoes.py` | Tipos, marcas, perfis, feriados, catálogos NSP, auditoria |
| `links` | `/links` | `app/routes/links.py` | Links úteis |
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

## Models

Pasta `app/models/`. Os mais centrais:

| Módulo | Arquivo |
|---|---|
| Usuário, perfil | `usuario.py` |
| Unidade, vínculo | `unidade.py` |
| Sala | `sala.py` |
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
