# Como alterar o SIGUS

Código aberto (MIT) de Diego Bispo Fernandes ([dbixpo](https://github.com/dbixpo)). Quem recebe uma instalação mantém o servidor e o banco dela. O desenvolvimento do dia a dia fica numa cópia local, com PostgreSQL local.

## Fluxo

1. Branch a partir do `main` (ou o branch que a casa padronizar).
2. Mudança pequena e revisável. UI segue [docs/IDENTIDADE_VISUAL.md](docs/IDENTIDADE_VISUAL.md).
3. Schema: arquivo **novo** em `migrations/add_….py`, idempotente. Não edite migration antiga já rodada em produção.
4. Permissão nova: entrada em `SECOES` / `ACAO_PARA_SECAO_TIPO` e tela Gestão de Perfis.
5. Teste local em `http://localhost:5001/sigus/` com perfil de ponta **e** administrador (o menu muda).
6. Revisão. Publicar numa instalação que já roda: [ATUALIZACAO-SERVIDOR.md](ATUALIZACAO-SERVIDOR.md). O `.env` e o banco dessa instalação não saem da máquina dela.

## Não faça

- Commit de `.env`, senha, dump, upload, print de paciente
- `git push --force` no `main`
- `migrations/recriar_admin.py` em produção
- Restaurar dump de notebook em cima do banco de produção
- Remover o prefixo `/sigus` sem plano de IIS
- Copiar paleta “institucional antiga” ou fonte Bebas Neue nas telas novas
- Tratar `app/static/references/samu/` como código vivo do SIGUS

## Padrões úteis

- Rotas em blueprints (`app/routes/…`), models em `app/models/…`
- Checagem de acesso: `current_user.pode('…')` + `abort(403)`
- POST com CSRF (`csrf_token()` no form)
- Impressos no modal padrão, não `window.print` solto em página crua (exceto relatórios que já têm botão Imprimir próprio)
- Data/hora e dinheiro pelos filtros Jinja já registrados (`br_datetime`, `br_currency`)

## Testes

Não há suíte automatizada completa neste repo. A verificação é: ambiente local + conferência das telas do módulo +, em produção, o checklist da entrega (login, unidade, um fluxo feliz, um fluxo de permissão negada).
