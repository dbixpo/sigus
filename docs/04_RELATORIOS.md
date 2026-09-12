# Relatórios e Exportações

## Visão Geral

O módulo de relatórios oferece consultas filtradas e exportações em **Excel (XLSX)** e **CSV**.

---

## Relatórios Disponíveis

Prefixo da aplicação: `/sigus`. Rotas abaixo são relativas a esse prefixo.

| Relatório | Rota | Descrição |
|-----------|------|-----------|
| Índice | `/relatorios/` | Hub com cards |
| Inventário | `/relatorios/inventario` | Equipamentos por unidade/sala |
| Salas | `/relatorios/salas` | Salas por unidade; filtro de chamado aberto |
| Contratos | `/relatorios/contratos` | Contratos vigentes |
| Profissionais | `/relatorios/profissionais` | Profissionais por unidade |
| Empenhos | `/relatorios/empenhos` | Controle financeiro (ContratoFinanceiro) |
| Segurança do Paciente | `nsp.relatorios` (`/seguranca-paciente/relatorios`) | Notificações NSP |
| Chamados | `/relatorios/chamados` | Chamados da rede |
| Aniversariantes | `/relatorios/aniversariantes` | Aniversários do mês por unidade |
| Usuários | `/relatorios/usuarios` | Usuários do sistema |
| Unidades | `/relatorios/unidades` | Unidades |
| Faltas abonadas | `/relatorios/faltas-abonadas` | RH |
| Mapa da Saúde | `/relatorios/mapa-saude` (interno) e `/mapa-da-saude` (público) | Rede no mapa |

---

## Filtros Comuns

- **Unidade(s)** — Uma ou mais unidades
- **Tipo de unidade** — UBS, USF, UPA etc.
- **Status** — Vigente, Ativo, etc. (conforme relatório)

Os filtros respeitam as permissões do usuário: quem não tem `ver_todas_unidades` vê apenas suas unidades vinculadas.

---

## Exportação Excel (openpyxl)

- Cabeçalho estilizado (fonte branca, fundo azul)
- Largura automática das colunas
- Formato `.xlsx` com encoding UTF-8

### Exemplo de uso interno

```python
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Inventário"
_estilizar_cabecalho(ws, ['Unidade', 'Sala', 'Tipo', ...])
for item in itens:
    ws.append([...])
_autofit(ws)
return _xlsx_response(wb, "inventario")
```

---

## Exportação CSV

- Delimitador `;` (padrão brasileiro)
- Encoding UTF-8 com BOM para abertura correta no Excel BR
- Quoting em todos os campos

---

## Permissões

`emitir_relatorios`: perfis **Administrador**, **Gestor Central** e **Gestor de Área**.
