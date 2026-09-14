# Instalar o SIGUS (município novo ou servidor do zero)

Guia para **primeira instalação**. Se o SIGUS **já roda** e você só vai atualizar código, use [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md).

Instância de referência (Sorocaba): https://saudedigital.sorocaba.sp.gov.br/sigus

O SIGUS **não é prontuário**. Atendimento clínico continua no sistema da casa (em Sorocaba, o SISWEB).

---

## O que você precisa

| Item | Nota |
|---|---|
| Python **3.10 ou 3.11** (64 bits) | 3.12 costuma funcionar; não testamos 3.13 no IIS |
| PostgreSQL 14+ | Banco vazio chamado `sigus` (ou o nome que a TI padronizar) |
| Git | Clone deste repositório |
| Windows Server + IIS + [HttpPlatformHandler v1.2](https://www.iis.net/downloads/microsoft/httpplatformhandler) | Produção no padrão da casa |
| Ou, para piloto | `run.py` em Flask/Waitress sem IIS, ainda com `APPLICATION_ROOT=/sigus` |

**Não** restaure dump de outro município (nem o snapshot antigo de desenvolvimento, se ainda aparecer no histórico do Git). Dado de pessoa, CPF e unidade são daquela rede.

---

## 1. Código e venv

```powershell
git clone https://github.com/dbixpo/sigus.git
cd sigus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env`:

```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=     # python -c "import secrets; print(secrets.token_hex(32))"
DATABASE_URL=postgresql://usuario:senha@localhost:5432/sigus
APPLICATION_ROOT=/sigus
SIGUS_PORT=5001
SIGUS_BEHIND_PROXY=1
SIGUS_PUBLIC_HOST=seu-dominio.gov.br
```

Senha com `@` na URL: encode como `%40`. Lista: `.env.example` e [SEGREDOS_E_INTEGRACOES.md](SEGREDOS_E_INTEGRACOES.md).

Piloto no notebook, sem IIS: `FLASK_ENV=development`, `SIGUS_BEHIND_PROXY=0`.

---

## 2. Banco vazio

```powershell
psql -U postgres -c "CREATE DATABASE sigus;"
.\venv\Scripts\python.exe migrations\bootstrap_nova_instalacao.py
```

Isso cria as tabelas (`db.create_all`), pastas de upload e aplica seeds (CBO, identidade inicial, matriz de perfis, mural/comunicados, NSP, agenda).

Primeiro administrador (**só em banco sem admin que você queira preservar** — o script apaga administradores existentes):

```powershell
$env:SIGUS_ADMIN_EMAIL='admin@seu-municipio.gov.br'
$env:SIGUS_ADMIN_SENHA='uma-senha-forte'
.\venv\Scripts\python.exe migrations\recriar_admin.py
```

Em instalação já povoada, para trocar senha: `scripts/reset_usuario_sigus.py`.

---

## 3. Primeiro acesso

```powershell
.\venv\Scripts\python.exe run.py
```

Abra **http://localhost:5001/sigus/login** (o prefixo `/sigus` vale também no localhost).

Depois do login:

1. **Configurações → Identidade** (ou a tela equivalente): município, secretaria, domínio de e-mail, logos. A paleta SIGUS (#1A82B8 / #0D3B5E / Inter) é a identidade visual; não troque por outra marca “institucional antiga”.
2. Cadastre ao menos um **prédio** e uma **unidade** ativa.
3. Vincule o administrador à unidade (seletor do topo).
4. Cadastre tipos de sala/equipamento conforme a rede, ou comece pelo essencial e evolua.

Feriados: a seed traz o calendário usado em Sorocaba; ajuste em Configurações.

---

## 4. Produção no IIS (Windows)

Detalhe do `web.config`, pool e pastas: [SETUP.md](SETUP.md) (escrito para o servidor de Sorocaba; troque hostname, caminho físico e `SIGUS_PUBLIC_HOST`).

Resumo:

1. Pasta do clone = caminho físico do aplicativo `/sigus`.
2. Application Pool: **Nenhum código gerenciado**.
3. `web.config` com `processPath` no `venv\Scripts\python.exe` desta pasta.
4. Conta do pool grava em `logs\` e `app\static\uploads\`.
5. Reciclar o pool; testar `https://seu-dominio/sigus/login`.

---

## 5. O que **não** fazer

- Commitar `.env`, senha, dump, upload, print de paciente
- Restaurar dump de homologação em cima de produção
- Rodar `migrations/recriar_admin.py` em produção povoada
- Remover o prefixo `/sigus` sem mudar IIS, PWA e manuais
- Copiar dump da Prefeitura de Sorocaba para “acelerar” outro município

---

## 6. Depois de no ar

- Atualização: [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md)
- Transferência de TI: [CHECKLIST_TRANSFERENCIA.md](CHECKLIST_TRANSFERENCIA.md)
- Manuais da ponta (BookStack, se a casa tiver): [MANUAIS_ESTANTE.md](MANUAIS_ESTANTE.md)
- Comunicados / ciência: [COMUNICADOS.md](COMUNICADOS.md)

Licença: [LICENSE](../LICENSE) (MIT). Mantenha o aviso de copyright da Secretaria da Saúde de Sorocaba.
