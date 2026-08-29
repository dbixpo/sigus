# SIGUS — Instruções para Colocar o Sistema em Funcionamento no Servidor

**Objetivo:** Fazer o sistema rodar em **https://saudedigital.sorocaba.sp.gov.br/sigus** em um servidor Windows com IIS.

---

**Instrução:** Leia e execute cada etapa na ordem. Use a pasta raiz do projeto (onde estão `run.py`, `web.config`, `app/`). O caminho `C:\inetpub\wwwroot\sigus` é apenas exemplo.

---

---

## PRÉ-REQUISITOS (verificar antes)

- Windows Server com **IIS 8+** habilitado  
- **HttpPlatformHandler** v1.2 instalado: https://www.iis.net/downloads/microsoft/httpplatformhandler  
- **Python 3.10 ou 3.11** instalado (ex.: `C:\Python311\python.exe`)  
- **PostgreSQL** instalado e rodando  
- A pasta do projeto já copiada para o servidor (ex.: `C:\inetpub\wwwroot\sigus`)

---

## ETAPA 1 — Definir a pasta do projeto

A pasta do projeto é onde estão os arquivos `run.py`, `web.config`, `app/`, `requirements.txt`, etc.

**Exemplo:** `C:\inetpub\wwwroot\sigus`

Em todos os comandos abaixo, substitua `C:\inetpub\wwwroot\sigus` pelo caminho real se for diferente.

---

## ETAPA 2 — Criar pasta de logs

O `web.config` grava saída da aplicação em `.\logs\python.log`. Crie a pasta:

```powershell
cd C:\inetpub\wwwroot\sigus
New-Item -ItemType Directory -Force -Path .\logs
```

---

## ETAPA 3 — Ajustar o web.config (caminho do Python)

1. Abra o arquivo `web.config` na raiz do projeto.  
2. Localize a linha `processPath="C:\Python311\python.exe"`.  
3. Altere para o caminho correto do `python.exe` no servidor:
   - Se usar **venv**: `C:\inetpub\wwwroot\sigus\venv\Scripts\python.exe`  
   - Se usar Python global: `C:\Python311\python.exe` (ou o caminho real da instalação)

---

## ETAPA 4 — Criar ambiente virtual e instalar dependências

```powershell
cd C:\inetpub\wwwroot\sigus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se não quiser usar venv, instale globalmente:

```powershell
cd C:\inetpub\wwwroot\sigus
pip install -r requirements.txt
```

*(Nesse caso, use o caminho do Python global no `web.config`.)*

---

## ETAPA 5 — Criar o arquivo .env

1. Copie o arquivo `.env.example` para `.env`:

   ```powershell
   cd C:\inetpub\wwwroot\sigus
   Copy-Item .env.example .env
   ```

2. Gere uma SECRET_KEY segura:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Edite o arquivo `.env` e preencha:

   ```env
   FLASK_APP=run.py
   FLASK_ENV=production
   SECRET_KEY=<cole aqui a chave gerada no passo anterior>
   DATABASE_URL=postgresql://usuario:senha@host:5432/sigus
   ```

   Substitua `usuario`, `senha`, `host` e `sigus` pelos dados reais do PostgreSQL no servidor.

---

## ETAPA 6 — Configurar o banco de dados

O projeto inclui um dump completo do banco em `database\sigus_backup_*.sql`. Para restaurar:

1. Crie o banco (se ainda não existir):

   ```powershell
   psql -U postgres -c "CREATE DATABASE sigus;"
   ```

2. Restaure o dump:

   ```powershell
   cd C:\inetpub\wwwroot\sigus
   psql -U postgres -d sigus -f database\sigus_backup_20260307_1225.sql
   ```

   *(Se o nome do arquivo for diferente, use o que existir em `database\`.)*

**Se estiver restaurando um dump antigo** (com tabelas `planos`, `acoes_plano` etc.), execute após restaurar:

   ```powershell
   python migrations/alinhar_nomenclatura_banco.py
   ```

**Para atualizar o dump** (ex.: após alterações no banco local), execute na máquina de desenvolvimento:

```powershell
python scripts/clone_banco.py
```

O novo arquivo será salvo em `database\` com timestamp. Copie para o servidor e restaure conforme acima.

---

## ETAPA 7 — Configurar a aplicação no IIS

1. Abra o **Gerenciador do IIS** (digite `inetmgr` no executar ou em uma janela de comando).  
2. Expanda **Sites** e selecione o site que responde por **saudedigital.sorocaba.sp.gov.br**.  
3. Clique com o botão direito no site → **Adicionar Aplicativo**.  
4. Preencha:
   - **Alias:** `sigus`
   - **Pool de aplicativos:** crie um novo ou selecione um existente
   - **Caminho físico:** `C:\inetpub\wwwroot\sigus` (ou o caminho real da pasta do projeto)

5. No **Pool de Aplicativos** da aplicação `sigus`:
   - Clique com o botão direito → **Configurações avançadas**
   - **Versão do .NET CLR:** `Nenhum código gerenciado`
   - **Iniciar pool de aplicativos imediatamente:** `True`

6. **Permissões:** A conta do pool (ex.: `IIS AppPool\sigus` ou `IIS_IUSRS`) deve ter:
   - Leitura na pasta do projeto  
   - Leitura e gravação em `C:\inetpub\wwwroot\sigus\logs`  
   - Leitura na pasta do Python (ex.: `C:\Python311`)

---

## ETAPA 8 — Reiniciar o IIS e testar

```powershell
iisreset
```

Acesse no navegador: **https://saudedigital.sorocaba.sp.gov.br/sigus**

---

## EM CASO DE ERRO

1. **Log da aplicação:**  
   `C:\inetpub\wwwroot\sigus\logs\python.log`

2. **Visualizador de Eventos:**  
   Logs do Windows → Aplicativo

3. **Verificar se o HttpPlatformHandler está instalado:**  
   No IIS, em Módulos, deve aparecer `httpPlatformHandler`.

4. **Permissões:**  
   Garanta que a conta do Application Pool tem acesso à pasta do projeto, à pasta `logs` e ao executável do Python.

---

## RESUMO DAS ETAPAS

| # | Ação |
|---|------|
| 1 | Definir pasta do projeto |
| 2 | Criar pasta `logs` |
| 3 | Ajustar `processPath` no `web.config` (caminho do Python) |
| 4 | `python -m venv venv` e `pip install -r requirements.txt` |
| 5 | Copiar `.env.example` para `.env` e preencher SECRET_KEY e DATABASE_URL |
| 6 | Criar banco e restaurar backup OU executar schema + seed + migrações |
| 7 | Criar aplicação `sigus` no IIS (alias: sigus, path: pasta do projeto) |
| 8 | `iisreset` e acessar https://saudedigital.sorocaba.sp.gov.br/sigus |
