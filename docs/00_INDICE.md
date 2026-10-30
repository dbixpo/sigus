# Índice da documentação técnica — SIGUS

Leia na ordem se estiver assumindo o sistema. Depois use a tabela como mapa.

1. [Instalação do zero](INSTALACAO.md) — banco vazio, primeiro admin, identidade
2. [Banco e migrations](BANCO.md) — PostgreSQL local, dump, o que não apontar para um servidor alheio
3. [Checklist de transferência](CHECKLIST_TRANSFERENCIA.md) — primeiro dia de quem for manter
4. [Visão geral](01_VISÃO_GERAL.md) — o que o SIGUS é e o que não é
5. [Arquitetura](ARQUITETURA.md) — Flask, prefixo `/sigus`, IIS, pastas
6. [Mapa do código](MAPA_DO_CODIGO.md) — blueprints, rotas, telas públicas
7. [Permissões e perfis](PERMISSOES.md)
8. [IIS](SETUP.md) — publicar num Windows Server, sem endereço fixo neste repositório
9. [Atualizar um servidor que já roda](../ATUALIZACAO-SERVIDOR.md)
10. [Segredos e integrações](SEGREDOS_E_INTEGRACOES.md)
11. [Identidade visual](IDENTIDADE_VISUAL.md)
12. [Manuais do usuário](MANUAIS_ESTANTE.md) — opcional, BookStack da instalação
13. [Como mudar o código](../CONTRIBUTING.md)

## Módulos (detalhe)

| Arquivo | Assunto |
|---|---|
| [02_CONTRATOS.md](02_CONTRATOS.md) | Contratos, mandado judicial, cobertura de equipamentos |
| [03_CONTROLE_EMPENHO.md](03_CONTROLE_EMPENHO.md) | Empenhos (`ContratoFinanceiro`) |
| [04_RELATORIOS.md](04_RELATORIOS.md) | Relatórios e exportação |
| [05_AUDITORIA.md](05_AUDITORIA.md) | Log de requisições |
| [SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md) | Fluxo do Núcleo (SNI-SGQSP): notificação pública e anônima, qualificação, comissões, coordenação liberada pelo Núcleo, SIS |
| [TRANSFERENCIAS_E_LOJINHA.md](TRANSFERENCIAS_E_LOJINHA.md) | Termos, aceite, Lojinha Interna |
| [COMUNICADOS.md](COMUNICADOS.md) | Recados, ciência por perfil **ou** CBO, editar/excluir comunicado e mural |
| [AGENDA_E_PLANEJAMENTOS.md](AGENDA_E_PLANEJAMENTOS.md) | Agenda estilo Google, ausência/férias, arrastar eventos, prazos editáveis com histórico |
| [PADRAO_SALAS_EQUIPAMENTOS.md](PADRAO_SALAS_EQUIPAMENTOS.md) | Ambientes padrão (AMB), catálogo de itens (ITEM), kit por tipo de sala, importação da planilha do Planejamento e relatório de aderência |
| [FREQUENCIA_RH.md](FREQUENCIA_RH.md) | Importar a planilha de frequência, Meus apontamentos, banco de horas, horas extras e de-para função × CBO |
| [METABASE.md](METABASE.md) | Painéis do Metabase no menu, apresentação, pedido de acesso e chave que não entra no Git |
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
├── database/            # sigus_inicial.sql (base pública, sem pessoas e sem chave); backups ficam fora do Git
├── docs/                # Esta documentação
├── migrations/          # Scripts Python one-shot (não é Alembic)
├── scripts/             # Operação: dump, restore, publicações
├── ATUALIZACAO-SERVIDOR.md
├── PRODUCAO-CURSOR.md   # texto para colar no Cursor do servidor
├── LICENSE              # MIT
├── CONTRIBUTING.md
└── README.md
```
