# Checklist — assumir o SIGUS

Use no primeiro dia em que outra pessoa for manter uma instalação. O repositório é o código (MIT, Diego Bispo Fernandes / [dbixpo](https://github.com/dbixpo)). Servidor, senha e banco **não** estão aqui. Anote o que falta num caderno da equipe, não neste arquivo.

## Acesso (fora do Git)

- [ ] Clone de https://github.com/dbixpo/sigus
- [ ] Acesso ao Windows Server onde o IIS publica o aplicativo `/sigus` (caminho físico: olhar no IIS, não neste repositório)
- [ ] Conta PostgreSQL daquela instalação (host, porta, banco, usuário). A URL fica só no `.env` do servidor
- [ ] Nome do pool IIS (CLR = Nenhum código gerenciado) e permissão de escrita em `logs\` e `app\static\uploads\`
- [ ] Se a busca de paciente no NSP estiver ligada: caminho e credenciais do robô (`SIS_CONSULTA_PATH`, `SIS_USUARIO`, `SIS_SENHA`) — **nunca no Git**

## Conferir no servidor (sem alterar ainda)

1. `git status` e `git log -1` na pasta da aplicação.
2. Existe `.env`? Tem `SECRET_KEY` forte, `DATABASE_URL` **dessa** máquina, `FLASK_ENV=production`, `APPLICATION_ROOT=/sigus`?
3. `SIGUS_BEHIND_PROXY=1` e `SIGUS_PUBLIC_HOST` com o host público **dessa** instalação?
4. `web.config` aponta para o `python.exe` do venv desta pasta?
5. `logs\python.log` gira?
6. Pastas de upload existem (gitignore; o processo precisa gravar)?
7. Abrir o login no host da instalação: entrar, escolher unidade, abrir um chamado e uma ficha de unidade.

## Rotina depois de assumir

- Atualização de código: [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md)
- Schema novo: `migrations/add_….py` idempotente, citado no que for entregue
- Senha de usuário: `scripts/reset_usuario_sigus.py`
- **Não** rode `migrations/recriar_admin.py` num banco que já tem gente (ele apaga todos os administradores)

## Troca de guarda

- [ ] Trocar a senha do administrador da aplicação (não reutilizar senha que tenha aparecido em script, chat ou notebook)
- [ ] `git check-ignore -v .env` no servidor — o `.env` não pode estar no Git
- [ ] Dumps e uploads dessa instalação não estão no Git
- [ ] Anotar, fora deste repositório, o caminho do site no IIS e o nome do pool

## Desenvolvimento em outro computador

Quem mexe no código usa PostgreSQL **local** e o `.env` de [`.env.example`](../.env.example). A `DATABASE_URL` do notebook não é a do servidor. Passo a passo: [BANCO.md](BANCO.md) (seção "Levar esta instalação para outro computador") e o README. Banco vazio: `migrations/bootstrap_nova_instalacao.py`. Cópia dos dados: dump local com `scripts/clone_banco.py` e restore com `scripts/restaura_banco.py` — o arquivo do dump fica de fora do Git.
