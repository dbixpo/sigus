# Script para o Cursor no ambiente de produção

Cole isto no chat do Cursor **no servidor** onde o SIGUS já roda (IIS + PostgreSQL). Não invente NSP, chamado, comunicado de teste nem usuário novo. Não commite `.env`. Não faça `git push --force`.

---

Você está no **servidor de produção do SIGUS** (Windows Server, IIS + HttpPlatformHandler, prefixo `/sigus`). Caminho físico: confira no IIS; o exemplo da documentação é `C:\inetpub\wwwroot\sigus`.

Objetivo desta entrega: atualizar o código do `main`, aplicar o que faltar no banco para **comunicados (ciência por perfil OU CBO)** e garantir **`tzdata`** (horário de Brasília). Não criar dado de teste.

## 1. Conferir o estado

```powershell
cd C:\inetpub\wwwroot\sigus
git status
git log -1 --oneline
git pull origin main
```

Se `git status` mostrar alteração local inesperada, **pare** e avise. Não dê `reset --hard` sem backup e autorização.

## 2. Dependências

O `requirements.txt` passou a incluir `tzdata` (Windows precisa disso para `ZoneInfo('America/Sao_Paulo')`). Sem esse pacote o Flask pode cair no boot.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Pastas de upload (gitignore)

```powershell
New-Item -ItemType Directory -Force -Path app\static\uploads\nsp, app\static\uploads\chamados, app\static\uploads\identidade, app\static\uploads\comunicados, app\static\uploads\acoes, app\static\uploads\perfis, logs
```

## 4. Banco — só o que esta entrega precisa

Com o `.env` **de produção** (não troque `DATABASE_URL`):

```powershell
.\venv\Scripts\python.exe migrations\add_ciencia_filtros.py
```

Isso cria, se ainda não existirem, as colunas TEXT `ciencia_perfis` e `ciencia_cbos` em `comunicados`. O script é idempotente. **Não** rode `recriar_admin.py`, `restaura_banco.py` nem dump.

Se o mural de comunicados **nunca** foi instalado neste banco (ambiente atrasado), na ordem:

```powershell
.\venv\Scripts\python.exe migrations\add_noticias_mural.py
.\venv\Scripts\python.exe migrations\add_ciencia_auditoria.py
.\venv\Scripts\python.exe migrations\add_ciencia_cpf.py
.\venv\Scripts\python.exe migrations\add_mural_social.py
.\venv\Scripts\python.exe migrations\add_lojinha_destino.py
.\venv\Scripts\python.exe migrations\add_ciencia_filtros.py
```

Não rode a pasta `migrations\` inteira “por garantia”.

## 5. Reinício

Recicle o Application Pool `sigus` (ou `iisreset` se for a política da casa). Abra `/sigus/login`.

## 6. Conferência (sem inventar dado)

1. Login e seletor de unidade.
2. Relógio no navbar = horário de Brasília.
3. Dashboard → **Novo comunicado**. Ordem: título → texto → anexo → unidade → cobrar ciência → quem (toda a equipe **ou** perfil **ou** CBO) → publicar.
4. Com a unidade da Secretaria / Saúde Digital selecionada, modo **Por CBO**: a lista deve trazer CBO de **cadastro e matrícula** (enfermeiro, fisioterapeuta etc.), não só quem tem CBO preenchido no cadastro SIGUS.
5. Um comunicado antigo com ciência continua abrindo; impresso no modal padrão.
6. Log: `.\logs\python.log` — se aparecer `ZoneInfoNotFoundError`, o `tzdata` não instalou no venv do IIS.

Playbook completo: `ATUALIZACAO-SERVIDOR.md`. Detalhe do recorte: `docs/COMUNICADOS.md`.
