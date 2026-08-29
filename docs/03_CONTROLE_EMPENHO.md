# Controle de Empenho (ContratoFinanceiro)

## Visão Geral

O módulo **Controle de Empenho** gerencia empenhos, reservas e fontes financeiras vinculados aos contratos, mapeando a planilha FINANCEIRO da DAG.

---

## Modelo ContratoFinanceiro

Tabela: `contrato_financeiro`

### Campos Principais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `contrato_id` | FK | Vínculo opcional com contrato |
| `tipo` | VARCHAR(50) | Indicar Despesa, Reserva, Reserva Complementar |
| `processo` | VARCHAR(100) | Processo SEI/CPL |
| `motivo` | VARCHAR(80) | Aditivo, Mandado Judicial, Prorrogação, etc. |
| `prestador` | VARCHAR(200) | Nome do prestador |
| `objeto` | TEXT | Objeto |
| `referencia` | VARCHAR(150) | Referência |
| `valor_total` | NUMERIC(14,2) | Valor total |

### Motivos Disponíveis

Aditivo, Aditivo MJ, Complemento, Mandado Judicial, Novo, Novo MJ, Prorrogação, Renovação, Serviço, Vigente, entre outros.

### Campos de Destinação

- `especializada`
- `vigilancia`
- `atencao_basica`
- `outros`
- `tabela_sus`
- `complemento`
- `emenda_municipal`, `emenda_estadual`, `emenda_federal`

### Datas e Controle

- `data_necessaria`
- `data_envio_divisao`
- `data_envio_fms`
- `data_devolucao_setor`
- `reservas`

---

## Rotas

- `/contratos/empenhos/` — Listagem com filtros (tipo, motivo)
- `/contratos/empenhos/novo` — Novo empenho
- `/contratos/empenhos/<id>/editar` — Editar
- `/contratos/empenhos/<id>/excluir` — Excluir (POST)

---

## Permissões

Cadastro/edição: perfil **Administrador** ou **Gestor Central** (via `cadastrar_contrato`/`editar_contrato`).
