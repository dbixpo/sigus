# Checklist — assumir o SIGUS

Use no primeiro dia em que a TI receber o repositório. Marque o que já estiver resolvido; o que faltar, resolva **antes** de mexer em produção.

## Acesso

- [ ] Clone de https://github.com/dbixpo/sigus (público) ou o remoto que a SES definir
- [ ] Acesso RDP / console no Windows Server onde o IIS responde `saudedigital.sorocaba.sp.gov.br`
- [ ] Caminho físico da aplicação no servidor (hoje, em geral sob `inetpub` ou pasta equivalente — **confira no IIS**, não neste arquivo)
- [ ] Conta PostgreSQL de produção (host, porta, banco `sigus`, usuário). A URL fica só no `.env` do servidor
- [ ] Pool IIS da aplicação `sigus` (CLR = Nenhum código gerenciado)
- [ ] Pasta de logs da aplicação e permissão de escrita da conta do pool
- [ ] Acesso à [Estante SES](https://estante-ses.sorocaba.sp.gov.br) se for atualizar manuais
- [ ] Se for manter a busca de paciente no NSP: caminho e credenciais do robô SIS (`SIS_CONSULTA_PATH`, `SIS_USUARIO`, `SIS_SENHA`) — **nunca no Git**

## Conferir no servidor (sem alterar ainda)

1. `git status` e `git log -1` na pasta da aplicação — deve estar no `main` (ou no branch que a casa usar).
2. Existe `.env`? Tem `SECRET_KEY` forte, `DATABASE_URL`, `FLASK_ENV=production`, `APPLICATION_ROOT=/sigus`?
3. `web.config` aponta para o `python.exe` certo (venv ou global)?
4. Pasta `logs\` existe e o `logs\python.log` gira?
5. `app\static\uploads\nsp` e demais pastas de upload existem (gitignore; o IIS precisa gravar)?
6. Abrir https://saudedigital.sorocaba.sp.gov.br/sigus/login — login, seletor de unidade, um chamado, uma ficha de unidade.

## Rotina depois de assumir

- Atualização de código: [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md)
- Schema novo: criar `migrations/add_….py` **idempotente** e documentar no PR / no playbook
- Senha de usuário: `scripts/reset_usuario_sigus.py` — **não** use `migrations/recriar_admin.py` em produção (ele apaga todos os administradores)

## Troca de guarda (obrigatório)

- [ ] Rotacionar a senha do administrador de aplicação (não reutilizar senha que já tenha aparecido em script, chat ou máquina de desenvolvimento)
- [ ] Confirmar que o `.env` de produção **não** está no Git (`git check-ignore -v .env`)
- [ ] Confirmar que dumps e uploads de produção **não** estão no Git
- [ ] Anotar neste checklist (ou na wiki da TI) o caminho real do site no IIS e o nome do Application Pool
