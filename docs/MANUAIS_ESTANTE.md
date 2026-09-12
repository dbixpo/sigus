# Manuais do usuário — Estante SES

A ponta **não** lê este repositório. O manual operacional está no BookStack da Secretaria:

**Livro:** [Manuais de utilização do SIGUS](https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sigus)  
`book_id = 45`

Tom: didático (“você”), caixas `callout info/warning/success`, passo a passo, print da tela. Espelha o livro de manuais do SISWEB.

Capítulo especial de patrimônio (salas, equipamentos, transferências, Lojinha): uma página por tela.

## Como republicar (máquina de quem edita o livro)

1. Prints: Chrome headless + Selenium no SIGUS **local** (`http://127.0.0.1:5001/sigus`), usuário de teste, **sem PII de paciente**.
2. Pasta temporária: `app/static/uploads/manuais_tmp/` (gitignore). Apague os PNG depois do upload.
3. Ambiente (nunca no Git):

   ```powershell
   $env:ESTANTE_EMAIL='...'
   $env:ESTANTE_SENHA='...'
   .\venv\Scripts\python.exe scripts\pub_estante_sigus.py
   .\venv\Scripts\python.exe scripts\pub_estante_patrimonio.py
   ```

Os scripts fazem login na sessão web da Estante e usam `/api/chapters`, `/api/pages`, `/api/image-gallery`. Capítulo existente é atualizado pelo nome; página existente idem.

Não subir print de notificação NSP com nome de cidadão. Não commitar credencial da Estante.
