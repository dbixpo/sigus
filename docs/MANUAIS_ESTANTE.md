# Manuais do usuário

A ponta não lê este repositório. Se a instalação quiser um livro no BookStack, os scripts `scripts/pub_estante_sigus.py` e `scripts/pub_estante_patrimonio.py` publicam o texto. A URL do livro e a do SIGUS **não** ficam no código: vêm do ambiente.

Tom: didático (“você”), caixas `callout info/warning/success`, passo a passo, print da tela.

## Como republicar

1. Prints: Chrome headless + Selenium no SIGUS **local** (`http://127.0.0.1:5001/sigus`), usuário de teste, sem dado real de paciente.
2. Pasta temporária: `app/static/uploads/manuais_tmp/` (gitignore). Apague os PNG depois do upload.
3. Ambiente (nunca no Git):

   ```powershell
   $env:ESTANTE_BASE = 'https://bookstack-da-instalacao'
   $env:SIGUS_PUBLIC_URL = 'https://dominio-da-instalacao/sigus'
   $env:ESTANTE_EMAIL = '...'
   $env:ESTANTE_SENHA = '...'
   .\venv\Scripts\python.exe scripts\pub_estante_sigus.py
   .\venv\Scripts\python.exe scripts\pub_estante_patrimonio.py
   ```

Os scripts fazem login na sessão web do BookStack e usam `/api/chapters`, `/api/pages`, `/api/image-gallery`. Capítulo existente é atualizado pelo nome; página existente idem.
