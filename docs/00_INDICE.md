# Índice Geral — Documentação SIGUS

Sistema de Gestão de Unidades de Saúde (SIGUS) — Documentação técnica e funcional.

---

## Documentos

| # | Arquivo | Descrição |
|---|---------|-----------|
| 01 | [01_VISÃO_GERAL.md](01_VISÃO_GERAL.md) | Visão do sistema e módulos principais |
| 02 | [02_CONTRATOS.md](02_CONTRATOS.md) | Módulo de contratos (planilha, mandado judicial) |
| 03 | [03_CONTROLE_EMPENHO.md](03_CONTROLE_EMPENHO.md) | Controle de empenho (ContratoFinanceiro) |
| 04 | [04_RELATORIOS.md](04_RELATORIOS.md) | Relatórios e exportações Excel |
| 05 | [05_AUDITORIA.md](05_AUDITORIA.md) | Módulo de auditoria |

**Deploy:** Use o guia [SETUP.md](SETUP.md) nesta pasta.

---

## Estrutura do Projeto

```
sigus/
├── app/           # Aplicação Flask
├── database/      # Dump do banco
├── docs/          # Documentação (esta pasta)
├── migrations/
├── scripts/
├── README.md
├── run.py
├── config.py
├── requirements.txt
├── web.config
└── .env.example
```
