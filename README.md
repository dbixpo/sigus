# SIGUS

Sistema de Gestão de Unidades de Saúde — Flask + PostgreSQL.

---

## 🚀 Como Rodar Localmente

### 1. Clonar o Repositório
```bash
git clone https://github.com/dbixpo/sigus.git
cd sigus
```

### 2. Criar Ambiente Virtual e Instalar Dependências
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar `.env`
Copie o arquivo de exemplo:
```bash
copy .env.example .env
```
Edite o `.env` e configure sua `DATABASE_URL`, por exemplo:
```env
DATABASE_URL=postgresql://postgres:suasenha@localhost:5432/sigus
```

### 4. Restaurar o Banco de Dados
Crie o banco `sigus` no seu PostgreSQL local e execute o script automático:
```bash
python scripts/restaura_banco.py
```
*(O script extrai automaticamente o arquivo `database/sigus_backup.zip` e carrega todos os dados no PostgreSQL).*

### 5. Iniciar a Aplicação
```bash
python run.py
```
Acesse em: `http://localhost:5001` (ou na porta configurada no seu `.env`).

---

**Para implantar no servidor:** veja [docs/SETUP.md](docs/SETUP.md).
