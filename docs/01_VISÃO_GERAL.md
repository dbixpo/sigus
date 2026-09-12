# Visão Geral do SIGUS

O **SIGUS** (Sistema Integrado de Gestão das Unidades de Saúde) é a aplicação web da **Saúde Digital** (Secretaria da Saúde de Sorocaba) para a gestão das unidades da rede municipal: patrimônio, chamados, pessoas, contratos, agenda, planejamentos e Segurança do Paciente.

Ele **não substitui o SISWEB**. Prontuário, consulta, SOAP, vacina e guia continuam lá. O SIGUS cuida do que faz a unidade funcionar.

Produção: https://saudedigital.sorocaba.sp.gov.br/sigus  
Manuais da ponta: [Estante SES](https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sigus)

Documentação técnica (TI): [00_INDICE.md](00_INDICE.md).

---

## Módulos

### Patrimônio

- **Prédios** — Edificações
- **Unidades** — UBS, USF, UPA, especialidades, etc. (ficha com abas)
- **Salas** — Ambientes por unidade (consultório, farmácia, recepção…). Há cadastro externo sem login para mutirão
- **Equipamentos** — Inventário por sala (patrimônio PMS-, marca/modelo, usuário, baixa)

### Operações

- **Chamados** — Manutenção (bem permanente amarra o equipamento)
- **Gestão de Chamados** — Fila de quem **executa** (setor + unidade prestadora)
- **Transferências** — Termos de empréstimo/transferência/doação e aceite com alocação em sala
- **Lojinha Interna** — Vitrine do que a unidade não usa mais
- **Contratos** — Vigência, mandado judicial, cobertura por tipo/marca/modelo
- **Controle de Empenho** — `ContratoFinanceiro`
- **Empresas** — Contratadas
- **SUEQ** — Emendas, licitações e chamados no schema `sueq`

### Gestão da unidade

- **Planejamentos** — Kanban com GUT
- **Agenda** — Compromissos e reuniões (feriados municipais)
- **Segurança do Paciente** — NSP interno, protocolo `SP-AAAA-NNNNN` ([SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md))
- **Links úteis**
- **Relatórios** — Inventário, salas, contratos, NSP, mapa da saúde, aniversariantes…

### Recursos humanos

- **Faltas abonadas** — Controle das 6 abonadas/ano (regra da casa)
- **Cadastro público de vínculo** — Pedido; coordenação aprova na ficha da unidade

### Configurações (administrador / autorizado)

Tipos de unidade/sala/equipamento, marcas e modelos, perfis, status de chamado, catálogos NSP, feriados, usuários, auditoria.

---

## Perfis

| Perfil | Uso típico |
|---|---|
| Administrador | Tudo, inclusive Gestão de Perfis e auditoria |
| Gestor Central | Rede, relatórios, contratos |
| Gestor de Área | Unidades vinculadas, planejamentos |
| Apoio Administrativo | Cadastros, patrimônio, chamados |
| Operador Padrão | Rotina da unidade |

O menu ainda depende da matriz Ver/Editar/Adicionar. Detalhe: [PERMISSOES.md](PERMISSOES.md).

---

## Tecnologias

- Backend: Flask 3, SQLAlchemy 2, Flask-Login, Flask-WTF (CSRF)
- Banco: PostgreSQL
- Front: Bootstrap 5, Jinja2, Inter
- Produção: Waitress + IIS HttpPlatformHandler
- Exportação: openpyxl / CSV
- Integração opcional: robô SISWEB (`app/sis_consulta.py`)
