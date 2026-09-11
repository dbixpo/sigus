# Atualização no servidor (SIGUS)

Instruções para o agente no servidor da Saúde Digital. Objetivo: puxar o `main` do GitHub, aplicar as mudanças de banco e reiniciar o app. **Não** commitar dumps, uploads nem `.env`.

## 1. Código

Na pasta do repositório (`C:\Users\hardr\Documents\GitHub\sigus` ou o caminho equivalente neste servidor):

```
git status
git pull origin main
```

Se houver alteração local que não deve perder, avisar o usuário antes de descartar. Não fazer `push --force`. Não commitar `app/static/uploads/`, `database/*.sql` de dump, nem `.env`.

Dependências: se o `pull` não mudou `requirements.txt`, não precisa reinstalar o venv.

## 2. Banco de dados (PostgreSQL local)

Rodar **na raiz do repositório**, com o venv do SIGUS, **nesta ordem** (scripts são idempotentes: `IF NOT EXISTS` / `ON CONFLICT DO NOTHING`):

```
.\venv\Scripts\python.exe migrations\add_agenda.py
.\venv\Scripts\python.exe migrations\add_agenda_reunioes.py
.\venv\Scripts\python.exe migrations\add_feriados.py
```

### O que cada um faz

**`migrations/add_agenda.py`**
- Cria a tabela `agenda_eventos` (compromissos da unidade: título, local, início/fim, visibilidade unidade/pessoal).
- Copia permissões da seção `Planejamentos` para a seção nova `Agenda` em `perfil_permissoes` (quem já via/editava planejamento passa a poder a agenda).

**`migrations/add_agenda_reunioes.py`**
- Coluna `agenda_eventos.tipo` (`evento` ou `reuniao`).
- Tabela `agenda_evento_participantes` (N:N evento ↔ usuário).

**`migrations/add_feriados.py`**
- Tabela `feriados` (data, nome, tipo feriado/ponto facultativo, natureza, decreto, expediente parcial, ativo).
- Insere o calendário **2026** do Decreto municipal nº 30.713/2025 (não duplica se a data já existir).

Não rodar dump `database/sigus_backup.sql` nem `database/sueq_data.sql` neste passo.

SUEQ (emendas/licitações) entra no código desta atualização. O schema `sueq` **não** é criado por esses três scripts. Se as telas SUEQ ainda não existirem neste servidor e o usuário não pedir importação, não inventar carga de dados.

## 3. Reiniciar o aplicativo

O SIGUS neste computador roda em Flask + PostgreSQL, em produção atrás de IIS/HttpPlatformHandler (porta típica de dev: 5001, prefixo `/sigus`).

Depois das migrations:

1. Reiniciar o site no IIS (ou o processo `python run.py` se for o ambiente de teste).
2. Abrir `/sigus/agenda/` (precisa de permissão Agenda — admin já passa).
3. Abrir **Configurações → Feriados** e conferir 2026.
4. Abrir **Planejamentos**: o interruptor “pendências minhas” deve nascer **desmarcado**.

## 4. O que mudou no sistema (para conferir)

- **Agenda**: calendário, evento, reunião com participantes, sugestão de 5 horários (dias úteis 8h–17h, sem almoço, sem feriado), feriado em vermelho no calendário.
- **Feriados**: cadastro em Configurações (menu lateral **Feriados**).
- **Planejamentos**: preferência do filtro “pendências minhas” salva no navegador; padrão desmarcado.
- Menu lateral agrupado + busca (JS).
- Gestão de chamados: filtro de status padrão da listagem, com “ver todos”.

Se algo falhar no import (`sueq_bp` / `agenda_bp`), conferir se o `pull` trouxe `app/routes/agenda.py`, `app/routes/sueq.py` e os models.
