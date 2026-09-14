# Atualização do SIGUS no servidor

Playbook **recorrente**. Não é o guia de instalação (esse é [docs/SETUP.md](docs/SETUP.md)).

Ambiente: Windows, Flask + PostgreSQL, IIS + HttpPlatformHandler, prefixo `/sigus`. Produção: https://saudedigital.sorocaba.sp.gov.br/sigus

**Não** inventar dados de teste em produção (NSP, chamado, transferência). **Não** commitar `.env`, dump nem upload. **Não** fazer `git push --force` no `main`.

Substitua `C:\inetpub\wwwroot\sigus` pelo caminho físico real do aplicativo no IIS.

---

## 1. Código

```powershell
cd C:\inetpub\wwwroot\sigus
git status
git pull origin main
```

Se `git status` mostrar alteração local que vocês não esperavam, **pare** e resolva (stash, commit na TI, ou descarte com autorização). Não dê `reset --hard` sem backup.

Se o `requirements.txt` mudou:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Crie pastas de upload que o `.gitignore` omite, se ainda não existirem:

```powershell
New-Item -ItemType Directory -Force -Path app\static\uploads\nsp
New-Item -ItemType Directory -Force -Path app\static\uploads\chamados
New-Item -ItemType Directory -Force -Path app\static\uploads\identidade
New-Item -ItemType Directory -Force -Path app\static\uploads\comunicados
New-Item -ItemType Directory -Force -Path app\static\uploads\acoes
```

---

## 2. Banco (só o que a entrega pediu)

Na raiz, com o `.env` **de produção**:

```powershell
.\venv\Scripts\python.exe migrations\<script_desta_entrega>.py
```

Scripts são em geral idempotentes (`IF NOT EXISTS`). A lista **desta** entrega deve estar no PR ou no card.

Identidade da instalação (textos + galeria de assets):

```powershell
.\venv\Scripts\python.exe migrations\add_identidade_sistema.py
```

Dashboard da unidade + comunicados/mural de ações:

```powershell
.\venv\Scripts\python.exe migrations\add_noticias_mural.py
.\venv\Scripts\python.exe migrations\add_ciencia_auditoria.py
.\venv\Scripts\python.exe migrations\add_lojinha_destino.py
.\venv\Scripts\python.exe migrations\add_ciencia_cpf.py
.\venv\Scripts\python.exe migrations\add_mural_social.py
```

### Já aplicados na rede (não precisa repetir, a menos que o banco seja novo)

Segurança do Paciente:

```
migrations\add_nsp.py
migrations\add_nsp_sis.py
migrations\add_nsp_tipos_infra.py
```

Agenda / feriados:

```
migrations\add_agenda.py
migrations\add_agenda_reunioes.py
migrations\add_feriados.py
```

Não rode `scripts/restaura_banco.py` nem dump `database/sigus_backup*.sql` em produção como “atualização”.

Não rode `migrations/recriar_admin.py` em produção.

---

## 3. `.env` (quando a entrega pedir variável nova)

Copie chaves **novas** do `.env.example` para o `.env` do servidor. Não versionar senha.

Integração SIS (busca de paciente no NSP) — só se o robô existir neste servidor:

```
SIS_CONSULTA_PATH=<pasta do repositório api-consulta-usuario-sis neste servidor>
SIS_USUARIO=
SIS_SENHA=
SIS_AMBIENTE=producao
SIS_SSL_VERIFY=true
```

Sem isso, o NSP continua abrindo: os campos de paciente ficam manuais.

Reinicie o processo Flask/IIS depois de editar `.env`.

---

## 4. Reinício

1. Recicle o Application Pool `sigus` (ou `iisreset` se for a política da casa).
2. Abra `/sigus/login`.
3. Confira o módulo da entrega (ex.: Segurança do Paciente, Transferências, Relatórios).
4. Impressos devem abrir no **modal** padrão do SIGUS, não numa página crua.

Log: `.\logs\python.log`

---

## 5. Conferência rápida pós-deploy

- Login e seletor de unidade no topo
- Ficha de uma unidade (abas Salas / Equipamentos)
- Um chamado (abrir ou ver fila, conforme perfil)
- Se a entrega foi NSP: `/sigus/seguranca-paciente/` e Configurações → Segurança do Paciente
- Se a entrega foi patrimônio: `/sigus/transferencias/?aba=lojinha`

Manuais da ponta (Estante) são outro passo: [docs/MANUAIS_ESTANTE.md](docs/MANUAIS_ESTANTE.md).
