# Segredos e integrações

Nada disto entra no Git: senha, `SECRET_KEY`, dump com dado real, print com PII de paciente.

## `.env`

Modelo versionado: `.env.example`. Cópia real: `.env` (gitignore).

| Variável | Obrigatória | Função |
|---|---|---|
| `SECRET_KEY` | Sim (produção) | Sessão e CSRF. Gerar com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Sim | `postgresql://user:senha@host:5432/sigus` — `@` na senha → `%40` |
| `FLASK_ENV` | Sim | `production` no IIS; `development` no notebook |
| `FLASK_APP` | Não | `run.py` |
| `APPLICATION_ROOT` | Sim na prática | `/sigus` (também no `web.config`) |
| `SIGUS_PORT` | Dev | Padrão `5001` (evitar 5000) |
| `HTTP_PLATFORM_PORT` | IIS | Injetada pelo HttpPlatformHandler |
| `SIGUS_BEHIND_PROXY` | Produção | Padrão `1`. Use `0` só em localhost sem IIS |
| `SIGUS_PUBLIC_HOST` | No servidor | Host público daquela instalação (CSRF e links). Vazio no notebook. Não versionar |
| `SIS_CONSULTA_PATH` | NSP com busca | Pasta do robô `api-consulta-usuario-sis` **neste** servidor |
| `SIS_USUARIO` / `SIS_SENHA` | NSP com busca | Credencial SISWEB |
| `SIS_AMBIENTE` | NSP | `producao` ou o que o robô esperar |
| `SIS_SSL_VERIFY` | NSP | `true` em produção |
| `ESTANTE_EMAIL` / `ESTANTE_SENHA` | Só na máquina que publica manuais | BookStack; não precisa existir no IIS |
| `METABASE_SITE_URL` | Não | URL https do Metabase daquela instalação. Se vazia, vale o que estiver em Configurações → Metabase |
| `METABASE_SECRET_KEY` | Não | Chave de incorporação. O `add_metabase.py` só grava se o campo no banco ainda estiver vazio. Não versionar |

`SECRET_KEY` default insegura em `config.py` (`sigus-dev-key-insegura`) — **só** desenvolvimento. Produção sem chave própria = sessão previsível.

## SISWEB (paciente no NSP)

Repositório à parte, em geral irmão deste na pasta GitHub da casa: `api-consulta-usuario-sis`. O SIGUS chama esse robô em `app/sis_consulta.py`. Se a pasta ou a senha faltarem, a notificação NSP **ainda abre**; o usuário digita o paciente na mão.

Não commitar `SIS_SENHA`. Não logar CPF/CNS em texto corrido.

## Manuais (BookStack, opcional)

Se a instalação publicar manuais num BookStack, a URL e o login ficam no ambiente da máquina que publica (`ESTANTE_BASE`, `ESTANTE_EMAIL`, `ESTANTE_SENHA`, `SIGUS_PUBLIC_URL`). Scripts: `scripts/pub_estante_sigus.py` e `scripts/pub_estante_patrimonio.py`. Ver [MANUAIS_ESTANTE.md](MANUAIS_ESTANTE.md). Nada disso entra no Git.

## Metabase

A chave de incorporação fica no `.env` da máquina ou na tabela `metabase_config`. O navegador só recebe o token assinado. `database/sigus_inicial.sql` pode trazer o dashboard de exemplo, com `secret_key` vazio. Quem for usar cola a chave da própria instalação. Detalhe: [METABASE.md](METABASE.md).

## Admin da aplicação

- Reset: `scripts/reset_usuario_sigus.py`
- `migrations/recriar_admin.py` exige `SIGUS_ADMIN_EMAIL` e `SIGUS_ADMIN_SENHA` e **apaga todos os administradores**. Não use em produção.

Se uma senha de admin já circulou em script antigo, **troque**.

## Auditoria

Quase todo HTTP autenticado vai para a tabela `auditoria`. Senhas devem ser sanitizadas em `parametros`. Detalhe: [05_AUDITORIA.md](05_AUDITORIA.md).
