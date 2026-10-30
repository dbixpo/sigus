# Visão Geral do SIGUS

O **SIGUS** (Sistema Integrado de Gestão das Unidades de Saúde) é o software livre de **Diego Bispo Fernandes** ([dbixpo](https://github.com/dbixpo)), licença MIT. Cobre patrimônio, chamados, pessoas, contratos, agenda, planejamentos, Segurança do Paciente e os painéis do Metabase.

Ele **não é prontuário**. Consulta, vacina e guia continuam no sistema clínico da rede. O SIGUS cuida do que faz a unidade funcionar. Nome da secretaria, município e logos ficam na identidade da instalação (banco), não no código.

Documentação técnica: [00_INDICE.md](00_INDICE.md). Licença: [LICENSE](../LICENSE).

---

## Módulos

### Patrimônio

- **Prédios** — Edificações
- **Unidades** — UBS, USF, UPA, especialidades, etc. (ficha com abas)
- **Salas** — Ambientes por unidade (consultório, farmácia, recepção…). Há cadastro externo sem login para mutirão
- **Equipamentos** — Inventário por sala (patrimônio PMS-, marca/modelo, usuário, baixa). Há cadastro externo sem login, com QR na ficha da unidade, para o mutirão do inventário inicial. Sem patrimônio e sem número de série, o cadastro e a edição exigem uma foto quadrada de 500×500, que a pessoa enquadra antes de salvar

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

- **Painel** (antigo Dashboard) — Comunicados com ciência (perfil **ou** CBO), mural de ações, aniversariantes, chamados abertos
- **Planejamentos** — Kanban com GUT
- **Agenda** — Estilo Google: compromissos, períodos e reuniões, arrastar para remarcar, reserva de veículos e de salas de reunião, prazos dos planejamentos e feriados municipais
- **Segurança do Paciente** — Fluxo do Núcleo (SNI-SGQSP): qualquer pessoa notifica, com ou sem login e de forma anônima; o Núcleo qualifica e encaminha às comissões das unidades; protocolo `SP-AAAA-XXXXXX` ([SEGURANCA_PACIENTE.md](SEGURANCA_PACIENTE.md))
- **Links úteis** — Lista com busca, versão pública sem login e QR code para baixar em cada link
- **Metabase** — Painéis incorporados no menu, visíveis conforme perfil, tipo de unidade e CBO. A apresentação troca sozinha; a chave de incorporação fica só na instalação ([METABASE.md](METABASE.md))
- **Relatórios** — Inventário, salas, contratos, NSP, mapa da saúde (com acesso público e QR code), aniversariantes…

### Recursos humanos

- **Faltas abonadas** — Controle das 6 abonadas/ano (regra da casa)
- **Cadastro público de vínculo** — Pedido; coordenação aprova na ficha da unidade

### Configurações (administrador / autorizado)

Tipos de unidade/sala/equipamento, marcas e modelos, perfis, status de chamado, membros do Núcleo e das comissões de Segurança do Paciente, feriados, usuários, auditoria.

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
