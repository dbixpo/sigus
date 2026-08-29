# Módulo de Auditoria

## Visão Geral

O módulo de auditoria registra automaticamente todas as requisições HTTP do sistema para fins de rastreabilidade e conformidade.

---

## Funcionamento

1. **Captura automática** — Via `after_request` e `teardown_request` no Flask
2. **Requisições autenticadas** — São gravadas com `usuario_id` do usuário logado
3. **Requisições anônimas** — Ex.: login (POST) — gravadas com `user_id` nulo
4. **Exclusões** — Apenas rotas estáticas (`static`) não são auditadas; todas as demais requisições são registradas

---

## Tabela `auditoria`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `created_at` | DATETIME | Data/hora do registro |
| `usuario_id` | INTEGER (nullable) | Usuário que fez a ação (null se anônimo) |
| `acao` | VARCHAR(50) | view, search, create, update, delete, export, print, login |
| `modulo` | VARCHAR(80) | contratos, chamados, configuracoes, etc. |
| `endpoint` | VARCHAR(200) | Nome da rota Flask |
| `url` | VARCHAR(500) | URL completa |
| `method` | VARCHAR(10) | GET, POST, PUT, DELETE |
| `parametros` | JSON | Query string e form (sanitizado) |
| `entity_type` | VARCHAR(80) | Tipo da entidade (ex: Contrato) |
| `entity_id` | INTEGER | ID da entidade afetada |
| `ip_address` | VARCHAR(45) | IP do cliente |
| `user_agent` | VARCHAR(500) | User-Agent do navegador |
| `response_status` | INTEGER | Código HTTP da resposta |
| `detalhes` | TEXT | Informações adicionais |

---

## Inferência de Ação e Módulo

- **ação** — Inferida pelo método HTTP e endpoint (GET → view, POST create/update/delete, etc.)
- **módulo** — Inferido pelo prefixo do blueprint (contratos, chamados, relatorios, auth, etc.)

---

## Interface de Consulta

- **Rota:** `/configuracoes/auditoria`
- **Acesso:** Apenas perfil **Administrador**
- **Funcionalidades:**
  - Listagem paginada
  - Filtros: data, usuário, ação, módulo, endpoint
  - Ordenação por data (mais recente primeiro)

---

## Segurança

- Registros não podem ser alterados ou excluídos pela aplicação
- Dados sensíveis (ex.: senhas) não devem ser incluídos em `parametros`
- O campo `parametros` é sanitizado para evitar gravação de tokens e senhas
