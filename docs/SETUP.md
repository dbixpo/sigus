# SIGUS — Produção no IIS (referência Sorocaba)

Objetivo na casa: a aplicação responder em **https://saudedigital.sorocaba.sp.gov.br/sigus** num Windows Server com IIS.

**Outro município / servidor do zero:** o passo a passo completo (clone, banco vazio, primeiro admin, identidade) está em [INSTALACAO.md](INSTALACAO.md). Este arquivo detalha o IIS no padrão da SES de Sorocaba.

Caminhos abaixo usam `C:\inetpub\wwwroot\sigus` como **exemplo**. No servidor real, use o caminho físico do aplicativo no IIS.

Para **atualizar** um SIGUS que já roda, não use este arquivo: use [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md).

---

## Pré-requisitos

- Windows Server, IIS 8+
- [HttpPlatformHandler v1.2](https://www.iis.net/downloads/microsoft/httpplatformhandler)
- Python **3.10 ou 3.11** (64 bits)
- PostgreSQL em execução
- Código do Git (`git clone` ou `git pull`) na pasta do site

---

## 1. Pasta e logs

```powershell
cd C:\inetpub\wwwroot\sigus
New-Item -ItemType Directory -Force -Path .\logs
New-Item -ItemType Directory -Force -Path .\app\static\uploads\nsp
New-Item -ItemType Directory -Force -Path .\app\static\uploads\chamados
```

A conta do Application Pool precisa gravar em `logs\` e em `app\static\uploads\`.

---

## 2. `web.config`

Ajuste `processPath` para o Python **desta** pasta:

- Recomendado: `C:\inetpub\wwwroot\sigus\venv\Scripts\python.exe`
- Ou o Python global, se for essa a política da casa

Não commitar um `web.config` com caminho da máquina de um desenvolvedor específico. O arquivo no Git é o modelo; o servidor pode ter caminho local (deixa o arquivo modificado **fora** do Git ou use o venv relativo à pasta).

---

## 3. Venv e dependências

```powershell
cd C:\inetpub\wwwroot\sigus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 4. `.env`

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Preencha no `.env` (nunca no Git):

```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=<chave gerada>
DATABASE_URL=postgresql://usuario:senha@host:5432/sigus
APPLICATION_ROOT=/sigus
SIGUS_PUBLIC_HOST=saudedigital.sorocaba.sp.gov.br
```

Senha com `@` na URL: encode como `%40`. Lista completa: `.env.example` e [SEGREDOS_E_INTEGRACOES.md](SEGREDOS_E_INTEGRACOES.md).

---

## 5. Banco

**Produção já existente:** restaure o **dump de produção** da própria rede (política de backup da TI) e aplique as migrations que faltarem. Não use dump de notebook.

**Servidor ou município do zero (banco vazio):**

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe migrations\bootstrap_nova_instalacao.py
```

Detalhes e primeiro admin: [INSTALACAO.md](INSTALACAO.md).

**Homologação com dump da própria casa:**

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe scripts\restaura_banco.py
```

O script procura `database\sigus_backup.zip` ou um `.sql` em `database\`. Dumps **não** entram no Git. Não restaure dump de outro município.

Se o dump for antigo (tabelas `planos` / `acoes_plano`):

```powershell
.\venv\Scripts\python.exe migrations\alinhar_nomenclatura_banco.py
```

---

## 6. IIS

1. Gerenciador do IIS → site `saudedigital.sorocaba.sp.gov.br` → **Adicionar Aplicativo**
2. Alias: `sigus`
3. Caminho físico: pasta do repositório
4. Pool dedicado, se possível:
   - Versão do .NET CLR: **Nenhum código gerenciado**
   - Iniciar imediatamente: True
5. Permissões: leitura na pasta do projeto; leitura+gravação em `logs` e `uploads`; execução do `python.exe`

---

## 7. Teste

```powershell
iisreset
```

Abrir https://saudedigital.sorocaba.sp.gov.br/sigus/login

## Se falhar

1. `.\logs\python.log`
2. Visualizador de Eventos → Aplicativo
3. Módulo `httpPlatformHandler` instalado no IIS
4. `DATABASE_URL` e PostgreSQL acessíveis a partir do servidor
5. Prefixo: a URL **precisa** incluir `/sigus`

Resumo rápido: pasta → venv → `.env` → banco → IIS → `iisreset`.
