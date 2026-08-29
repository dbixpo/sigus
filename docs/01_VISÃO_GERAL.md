# Visão Geral do SIGUS

## O que é o SIGUS

O **SIGUS** (Sistema de Gestão de Unidades de Saúde) é uma aplicação web para gestão de patrimônio, contratos, chamados e recursos humanos das unidades de saúde municipais.

---

## Módulos Principais

### Patrimônio
- **Prédios** — Cadastro de prédios das unidades
- **Unidades** — UBS, USF, UPA, Centros de Especialidades etc.
- **Salas** — Salas por unidade (consultório, farmácia, enfermagem)
- **Equipamentos** — Inventário por sala (computador, maca, ar-condicionado)

### Operações
- **Chamados** — Abertura e acompanhamento de chamados de manutenção
- **Gestão de Chamados** — Fila Kanban por setor de manutenção
- **Transferências** — Solicitação e aceite de transferência de equipamentos
- **Contratos** — Contratos vigentes, vigência, mandado judicial
- **Controle de Empenho** — Empenhos e fontes financeiras (ContratoFinanceiro)
- **Empresas** — Empresas contratadas

### Gestão
- **Planejamentos** — Projetos em Kanban com priorização GUT
- **Relatórios** — Inventário, salas, contratos, profissionais, exportação Excel

### Configurações (administrador)
- Tipos de unidade, sala, equipamento
- Marcas e modelos
- Perfis de acesso
- Status de chamados
- Links úteis
- Auditoria

### Recursos Humanos
- **Faltas Abonadas** — Registro e impressão de faltas

---

## Perfis de Usuário

| Perfil | Descrição |
|--------|-----------|
| Administrador | Acesso total, configurações, auditoria |
| Gestor Central | Todas as unidades, relatórios, contratos |
| Gestor de Área | Unidades vinculadas, planejamentos |
| Apoio Administrativo | Cadastro de equipamentos, chamados |
| Operador Padrão | Abertura de chamados |

---

## Tecnologias

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Banco:** PostgreSQL
- **Frontend:** Bootstrap 5, Jinja2
- **Exportação:** openpyxl (Excel), CSV
