# Relatórios e Exportações

## Visão Geral

O módulo de relatórios oferece consultas filtradas e exportações em **Excel (XLSX)** e **CSV**.

---

## Relatórios Disponíveis

Prefixo da aplicação: `/sigus`. Rotas abaixo são relativas a esse prefixo.

| Relatório | Rota | Descrição |
|-----------|------|-----------|
| Índice | `/relatorios/` | Hub com cards e busca pelo nome do relatório |
| Inventário | `/relatorios/inventario` | Equipamentos por unidade/sala, com filtro e coluna RENEM |
| Mural da Saúde | `/relatorios/mural` | Postagens do mural; período padrão dos últimos 30 dias. O botão gera o Boletim da Rede no modal de impressão (A4): a mais curtida na capa, as demais em duas colunas |
| Salas | `/relatorios/salas` | Salas por unidade; filtro de chamado aberto |
| Padrão de salas e equipamentos | `/relatorios/padrao-salas` | Aderência de cada sala ao kit do seu ambiente padrão: falta, sobra e custo estimado. Abas por unidade, necessidade por item, sala a sala (até 5 unidades) e a reclassificar. Excel com 4 abas. Ver [PADRAO_SALAS_EQUIPAMENTOS.md](PADRAO_SALAS_EQUIPAMENTOS.md) |
| Contratos | `/relatorios/contratos` | Contratos vigentes |
| Profissionais | `/relatorios/profissionais` | Profissionais por unidade |
| Base de servidores do RH | `/relatorios/base-rh` | Aba Banco de Dados da planilha de frequência. Uma matrícula por linha, com os dados da competência mais nova. Filtros: matrícula, nome, uma ou mais funções, um ou mais locais e planilha |
| Empenhos | `/relatorios/empenhos` | Controle financeiro (ContratoFinanceiro) |
| Segurança do Paciente | `nsp.relatorios` (`/seguranca-paciente/relatorios`) | Indicadores e painel na mesma página; Excel e CSV. Só Núcleo e comissões (card some para os demais) |
| Chamados | `/relatorios/chamados` | Chamados da rede |
| Aniversariantes | `/relatorios/aniversariantes` | Aniversários do mês por unidade |
| Usuários | `/relatorios/usuarios` | Usuários do sistema |
| Unidades | `/relatorios/unidades` | Unidades |
| Faltas abonadas | `/relatorios/faltas-abonadas` | RH |
| Mapa da Saúde | `/relatorios/mapa-saude` (interno) e `/mapa-da-saude` (público) | Rede no mapa. A tela interna tem os botões Acesso público, QR code e copiar endereço, sempre com o domínio oficial |

**Aniversariantes** (relatório e card do dashboard): entra todo usuário ativo com data de nascimento e vínculo ativo na unidade, de qualquer perfil. O perfil `administrador` ficava de fora e foi incluído.

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

## LGPD

Operador Padrão e Apoio Administrativo recebem CPF e telefone mascarados nos relatórios, na listagem de usuários, na ficha de falta abonada e no celular de quem criou ou aceitou uma transferência. A máscara do CPF guarda os três primeiros dígitos, o nono e os dois últimos. O telefone guarda o DDD e os dois últimos dígitos. Com a máscara, o link de WhatsApp não é montado.

Gestor de Área, Gestor Central e Administrador veem o dado completo. A ficha CNES e o e-mail CNES também saem completos, para qualquer perfil que possa emiti-los. Telefone institucional da unidade e o telefone do mapa público não entram nessa regra.

## Permissões

`emitir_relatorios`: perfis **Administrador**, **Gestor Central** e **Gestor de Área**.
