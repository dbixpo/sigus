# Identidade visual — Saúde Digital (SIGUS)

Qualquer tela, impresso ou material do SIGUS usa a identidade da **Saúde Digital / SIGUS**. Não inventar paleta, não usar a identidade antiga do site institucional (`#3b84b5` / Bebas Neue) como padrão.

## Cores

| Papel | Hex |
|---|---|
| Primary | `#1A82B8` |
| Secondary | `#19A88B` |
| Dark (navbar) | `#0D3B5E` |
| Accent red (coração) | `#E63030` |
| Accent yellow (coração) | `#F5C500` |
| Background | `#F4F6F9` |
| Text | `#1E3A50` |
| Muted | `#718096` |

Botão primário: `#1A82B8`, hover `#155d8c`, radius 6px. Cards brancos, radius 10–16px, sombra suave.

## Tipografia

**Inter**. Navbar: fundo `#0D3B5E`, borda inferior 3px `#1A82B8`.

## Logos

| Arquivo | Uso |
|---|---|
| `app/static/img/logo-sd-branco.png` | Fundo escuro (navbar, login faixa) |
| `app/static/img/logo-sd-colorido.png` | Fundo claro |

## Login / capa

Faixa no topo com gradiente 90deg vermelho / amarelo / azul.

## Páginas públicas e cartão de QR code

Páginas sem login (Links Úteis, notificação de Segurança do Paciente, Mapa da Saúde) seguem o mesmo padrão: faixa vermelho / amarelo / azul, topo `#0D3B5E` com borda `#1A82B8` e logo branca, fundo `#F4F6F9`.

O cartão de QR code baixado (PNG, 900 px de largura) tem a faixa no topo, título em `#0D3B5E` (Inter 700), "Aponte a câmera do celular para acessar" em `#718096`, QR em `#0D3B5E`, endereço em `#1E3A50` e rodapé "SIGUS · Saúde Digital" em `#1A82B8`. Gerado em `app/static/js/acesso-publico.js`; não monte outro estilo de QR.

## Onde está no código

- Casca autenticada: `app/templates/base.html`
- Login: `app/templates/auth/login.html`
- CSS: `app/static/css/`
- JS comum: `app/static/js/sigus.js`

Tela pública (cadastro externo, mapa) deve repetir a mesma paleta, mesmo que não estenda `base.html`.
