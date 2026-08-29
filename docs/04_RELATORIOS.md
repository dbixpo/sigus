# Relatórios e Exportações

## Visão Geral

O módulo de relatórios oferece consultas filtradas e exportações em **Excel (XLSX)** e **CSV**.

---

## Relatórios Disponíveis

| Relatório | Rota | Descrição |
|-----------|------|-----------|
| Índice | `/relatorios/` | Página inicial com links |
| Inventário | `/relatorios/inventario` | Equipamentos por unidade/sala |
| Salas | `/relatorios/salas` | Salas por unidade |
| Contratos | `/relatorios/contratos` | Contratos vigentes |
| Profissionais | `/relatorios/profissionais` | Profissionais por unidade |
| Empenhos | `/relatorios/empenhos` | Controle financeiro (ContratoFinanceiro) |

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
