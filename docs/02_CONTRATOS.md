# Módulo de Contratos

## Visão Geral

O módulo de contratos gerencia contratos vigentes das unidades de saúde, incluindo campos da planilha CONTRATOS ATUAL e indicador de mandado judicial.

---

## Campos da Planilha CONTRATOS ATUAL

Os contratos possuem campos mapeados da planilha oficial:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `secao` | VARCHAR(100) | Seção administrativa |
| `numero_contrato` | VARCHAR(50) | Nº do contrato (distinto de CPL/SEI) |
| `numero_sei` | VARCHAR(100) | Nº do Processo SEI |
| `link_sei` | VARCHAR(500) | Link de acesso direto do processo SEI |
| `cpl` | VARCHAR(30) | CPL formato numero/AAAA (ex: 424/2020) |
| `empresa` / `empresa_id` | VARCHAR / FK | Empresa contratada (texto ou vínculo) |
| `modalidade` | VARCHAR(80) | Compra Eletrônica, Concorrência, Pregão etc. |
| `tipo_contrato` | VARCHAR(100) | Tipo do contrato |
| `objeto` | TEXT | Objeto do contrato |
| `data_inicio` / `data_fim` | DATE | Vigência |
| `data_assinatura` | DATE | Data de assinatura |
| `vigencia` | VARCHAR(100) | Texto de vigência |
| `fonte` | VARCHAR(150) | Fonte do contrato |
| `valor_total` | NUMERIC(14,2) | Valor total |
| `valor_inicial` | NUMERIC(14,2) | Valor inicial |
| `valor_atual` | NUMERIC(14,2) | Valor atual |
| `valor_mensal_atual` | NUMERIC(14,2) | Valor mensal atual |
| `aditivo_data_pct` | VARCHAR(200) | Aditivo (Data e %) |
| `reajuste_data_base_pct` | VARCHAR(200) | Reajuste (Data base e %) |
| `fiscalizacao` | VARCHAR(200) | Fiscalização |
| `supressao_data_pct` | VARCHAR(200) | Supressão (Data e %) |
| `contato_nome_telefone` | VARCHAR(300) | Contato e telefone |
| `empenhos` | TEXT | Empenhos |
| `status` | VARCHAR(20) | vigente, a_vencer, vencido, encerrado |

---

## Mandado Judicial

O campo **`mandado_judicial`** (BOOLEAN) indica se o contrato é originado de mandado judicial. Substitui o uso anterior de tag para essa marcação.

- `false` (padrão): contrato regular
- `true`: contrato sob mandado judicial

---

## Equipamentos Cobertos

Cada contrato possui itens (`ContratoTipoEquipamento`) que definem a cobertura por:
- **Tipo** — Notebook, Ar-condicionado, etc.
- **Marca** — Dell, Philips, etc. (ou todas)
- **Modelo** — Latitude 5420, etc. (ou todos)

---

## Ações do Contrato

O modelo `ContratoAcao` registra:
- Prorrogação / Renovação
- Termo Aditivo
- Notificação / Multa
- Termo de Encerramento
