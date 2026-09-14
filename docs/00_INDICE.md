# Índice da documentação técnica — SIGUS

Leia na ordem se estiver assumindo o sistema. Depois use a tabela como mapa.

1. [Instalação do zero](INSTALACAO.md) — outro município ou servidor vazio
2. [Checklist de transferência](CHECKLIST_TRANSFERENCIA.md) — o que conferir no primeiro dia na casa
3. [Visão geral](01_VISÃO_GERAL.md) — o que o SIGUS é e o que não é
4. [Arquitetura](ARQUITETURA.md) — Flask, prefixo `/sigus`, IIS, pastas
5. [Mapa do código](MAPA_DO_CODIGO.md) — blueprints, rotas, telas públicas
6. [Permissões e perfis](PERMISSOES.md)
7. [Banco e migrations](BANCO.md)
8. [IIS (referência Sorocaba)](SETUP.md)
9. [Operação no servidor](../ATUALIZACAO-SERVIDOR.md)
10. [Segredos e integrações](SEGREDOS_E_INTEGRACOES.md)
11. [Identidade visual](IDENTIDADE_VISUAL.md)
12. [Manuais na Estante SES](MANUAIS_ESTANTE.md)
13. [Como mudar o código](../CONTRIBUTING.md)

## Módulos (detalhe)

| Arquivo | Assunto |
|---|---|
| [02_CONTRATOS.md](02_CONTRATOS.md) | Contratos, mandado judicial, cobertura de equipamentos |
| [03_CONTROLE_EMPENHO.md](03_CONTROLE_EMPENHO.md) | Empenhos (`ContratoFinanceiro`) |
| [04_RELATORIOS.md](04_RELATORIOS.md) | Relatórios e exportação |
| [05_AUDITORIA.md](05_AUDITORIA.md) | Log de requisições |
| [SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md) | NSP interno, protocolo `SP-AAAA-NNNNN`, SIS |
| [TRANSFERENCIAS_E_LOJINHA.md](TRANSFERENCIAS_E_LOJINHA.md) | Termos, aceite, Lojinha Interna |
| [COMUNICADOS.md](COMUNICADOS.md) | Recados, ciência por perfil **ou** CBO |
| [INSTALACAO.md](INSTALACAO.md) | Clone, banco vazio, primeiro admin, identidade |
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
├── PRODUCAO-CURSOR.md   # texto para colar no Cursor do servidor
├── LICENSE              # MIT
├── CONTRIBUTING.md
└── README.md
```
