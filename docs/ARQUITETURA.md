# Arquitetura do SIGUS

## Visão em uma frase

Aplicação **Flask** monolítica, templates **Jinja2**, banco **PostgreSQL**, autenticada com **Flask-Login** e CSRF (**Flask-WTF**). Em produção roda com **Waitress** atrás do **IIS** (módulo **HttpPlatformHandler**), sempre sob o prefixo **`/sigus`**.

```
Navegador
    → IIS (HTTPS, site saudedigital.sorocaba.sp.gov.br)
        → aplicativo /sigus  (web.config → python run.py)
            → Waitress  (porta HTTP_PLATFORM_PORT)
                → PrefixMiddleware (/sigus)
                    → Flask (blueprints em app/routes/)
                        → SQLAlchemy → PostgreSQL
```

## Entry points

| Arquivo | Papel |
|---|---|
| `run.py` | Cria a app, aplica `ProxyFix`, injeta host público se o IIS reescrever para localhost (CSRF), escolhe porta, sobe Flask debug ou Waitress |
| `app/__init__.py` | `create_app()`: CSRF, login, blueprints, filtros Jinja, seletor de unidade, guarda de vínculo |
| `config.py` | Lê `.env` (`SECRET_KEY`, `DATABASE_URL`) |
| `web.config` | HttpPlatformHandler, `APPLICATION_ROOT=/sigus`, `FLASK_ENV=production`, log em `.\logs\python.log` |

`Flask-Migrate` está no `requirements.txt`, mas **o time não usa Alembic no dia a dia**. Evolução de schema = script Python em `migrations/` (idempotente). Ver [BANCO.md](BANCO.md).

## Prefixo `/sigus`

`APPLICATION_ROOT=/sigus` está no `web.config` e no `run.py` (`setdefault`). O `PrefixMiddleware` corta o prefixo do `PATH_INFO` e preenche `SCRIPT_NAME`. Por isso:

- URL pública: `https://saudedigital.sorocaba.sp.gov.br/sigus/login`
- URL local: `http://localhost:5001/sigus/login`
- `url_for` e estáticos já nascem com `/sigus`

Não remova o prefixo “para simplificar” sem mudar IIS, `web.config`, PWA (`manifest.json`) e todos os manuais.

## Camadas

```
app/
├── models/          # SQLAlchemy (uma classe ≈ uma tabela)
├── routes/          # Blueprints (HTTP)
├── templates/       # Jinja2 (base.html = casca SIGUS)
├── static/          # css/, js/sigus.js, img/ (logos), uploads/ (não versionar)
├── utils.py         # Filtros de data, moeda, telefone BR
└── sis_consulta.py  # Ponte com o robô do SISWEB (NSP)
```

Padrão de tela autenticada: `templates/base.html` (navbar `#0D3B5E`, Inter, paleta Saúde Digital). Telas **públicas** (cadastro externo, chamado externo, mapa) têm HTML próprio.

## Autenticação e CSRF

- Login: e-mail (completa `@sorocaba.sp.gov.br` se o usuário omitir o domínio) + senha.
- Sessão Flask-Login; “Lembrar-me” usa cookie persistente.
- CSRF em todos os POST autenticados. Em produção, se o IIS mandar `Host: localhost`, o `run.py` injeta `X-Forwarded-Host` = `SIGUS_PUBLIC_HOST` (padrão `saudedigital.sorocaba.sp.gov.br`) para o token não quebrar. Desligue só em dev puro: `SIGUS_BEHIND_PROXY=0`.

## Unidade de trabalho

Quem não é administrador “solto” precisa de **vínculo** (`usuario_unidade`). O seletor do topo grava `usuarios.unidade_padrao_id`. Chamados, NSP, lojinha e aceite de transferência usam essa unidade. Detalhe: [PERMISSOES.md](PERMISSOES.md).

## Uploads

Arquivos de usuário ficam em `app/static/uploads/` (chamados, NSP, fotos de perfil, SUEQ). Pastas no `.gitignore`. O pool do IIS precisa **gravar** nesses diretórios. Limite de body no IIS: 100 MB (`web.config`). Anexos NSP: 10 MB no código.

## O que não está neste repo

- **SISWEB** (prontuário) — sistema à parte; o SIGUS só consulta paciente via robô opcional.
- **Estante SES** (BookStack) — manuais; scripts em `scripts/pub_estante_*.py`.
- **Referência SAMU** em `app/static/references/samu/` — código de outro sistema, **não** é executado pelo SIGUS. Não trate como módulo ativo.
