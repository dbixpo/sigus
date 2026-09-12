# Índice da documentação técnica — SIGUS

Leia na ordem se estiver assumindo o sistema. Depois use a tabela como mapa.

1. [Checklist de transferência](CHECKLIST_TRANSFERENCIA.md) — o que conferir no primeiro dia
2. [Visão geral](01_VISÃO_GERAL.md) — o que o SIGUS é e o que não é
3. [Arquitetura](ARQUITETURA.md) — Flask, prefixo `/sigus`, IIS, pastas
4. [Mapa do código](MAPA_DO_CODIGO.md) — blueprints, rotas, telas públicas
5. [Permissões e perfis](PERMISSOES.md)
6. [Banco e migrations](BANCO.md)
7. [Primeira instalação](SETUP.md)
8. [Operação no servidor](../ATUALIZACAO-SERVIDOR.md)
9. [Segredos e integrações](SEGREDOS_E_INTEGRACOES.md)
10. [Identidade visual](IDENTIDADE_VISUAL.md)
11. [Manuais na Estante SES](MANUAIS_ESTANTE.md)
12. [Como mudar o código](../CONTRIBUTING.md)

## Módulos (detalhe)

| Arquivo | Assunto |
|---|---|
| [02_CONTRATOS.md](02_CONTRATOS.md) | Contratos, mandado judicial, cobertura de equipamentos |
| [03_CONTROLE_EMPENHO.md](03_CONTROLE_EMPENHO.md) | Empenhos (`ContratoFinanceiro`) |
| [04_RELATORIOS.md](04_RELATORIOS.md) | Relatórios e exportação |
| [05_AUDITORIA.md](05_AUDITORIA.md) | Log de requisições |
| [SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md) | NSP interno, protocolo `SP-AAAA-NNNNN`, SIS |
| [TRANSFERENCIAS_E_LOJINHA.md](TRANSFERENCIAS_E_LOJINHA.md) | Termos, aceite, Lojinha Interna |
| [migrations/README.md](../migrations/README.md) | Scripts idempotentes de schema |
| [scripts/README.md](../scripts/README.md) | Dump, restore, Estante, SUEQ, reset de senha |

## Estrutura do repositório

```
sigus/
├── app/                 # Flask: models, routes, templates, static
├── config.py            # Configuração (lê .env)
├── run.py               # Entry point (dev + Waitress)
├── web.config           # IIS / HttpPlatformHandler
├── requirements.txt
├── .env.example         # Modelo — copiar para .env (nunca versionar o .env)
├── database/            # Dump ZIP de desenvolvimento; dumps .sql ficam fora do Git
├── docs/                # Esta documentação
├── migrations/          # Scripts Python one-shot (não é Alembic)
├── scripts/             # Operação: dump, restore, publicações
├── ATUALIZACAO-SERVIDOR.md
├── CONTRIBUTING.md
└── README.md
```
