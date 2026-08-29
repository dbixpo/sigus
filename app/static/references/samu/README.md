# Sistema SAMU 192

Sistema de Regulação e Gestão do Serviço de Atendimento Móvel de Urgência, inspirado no ESUSSAMU e ESUS APS.

## Tecnologias

- **Backend:** Python / Flask
- **Banco de dados:** PostgreSQL
- **Frontend:** HTML, CSS (Bootstrap 5), JavaScript

## Identidade Visual

Conforme manual de padronização do SAMU:
- **Vermelho** (Pantone 186): `#c20d2f` — navbar superior
- **Laranja** (Pantone 717): `#dd8d0c` — menu lateral

## Perfis de Usuário

| Perfil | Descrição |
|--------|-----------|
| Administrador | Administra o sistema e configurações |
| TARM | Atende ligações e registra solicitações |
| Rádio Operador | Gestão de ocorrências e despacho de viaturas |
| Médico Regulador | Regulação das ligações e decisões clínicas |
| Médico Intervencionista | Registra atendimento aos pacientes |
| Enfermeiro | Registra atendimento aos pacientes |
| Aux./Téc. Enfermagem | Registra atendimento aos pacientes |
| Condutor | Recebe chamados e garante ida/volta |

## Instalação

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variáveis de ambiente** (criar `.env`):
   ```
   DATABASE_URL=postgresql://postgres:%40Qweszxc7895123@localhost/samu
   SECRET_KEY=sua-chave-secreta
   ```

3. **Criar o banco e estrutura** (PostgreSQL em execução):
   ```bash
   python database/executar.py
   ```
   Cria o banco `samu`, tabelas, Unidade SAMU padrão e usuário admin.

4. **Executar:**
   ```bash
   python run.py
   ```

   Acesse: http://localhost:5192

   **Login padrão:** administrador.sd / @Qweszxc7895123

## Deploy atrás de proxy reverso (IIS em subpath)

Para servir em `https://saudedigital.sorocaba.sp.gov.br/samu`:

1. **Configure o IIS** para fazer proxy reverso de `/samu` para `http://localhost:5192`
2. **Defina a variável de ambiente** no servidor:
   ```
   APPLICATION_ROOT=/samu
   ```
3. Todos os links (`url_for`) e redirects serão gerados com o prefixo `/samu` automaticamente.

Em desenvolvimento local (`localhost:5192`), não defina `APPLICATION_ROOT` — tudo continua funcionando na raiz.

## Estrutura do Projeto

```
samu/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   ├── routes/          # Blueprints (auth, dashboard, configuracoes, rh)
│   ├── static/          # CSS, JS, imagens
│   └── templates/       # Templates Jinja2
├── database/            # Estrutura e scripts do banco
│   ├── 01_schema.sql    # CREATE TABLE
│   ├── 02_dados_iniciais.sql
│   ├── executar.py      # Script único para criar tudo
│   └── README.md
├── scripts/             # Scripts de utilidade
├── config.py
├── run.py
└── requirements.txt
```

## Módulos

### Configuração (apenas Administrador)
- Profissional
- Unidades SAMU
- Unidades de Saúde
- Tipo de Ligação
- Origem de Ligação
- Algoritmo de Acolhimento
- CID-10
- Tipo de Ocorrência
- Motivo de Ocorrência
- Intercorrência

### Recursos Humanos
- Faltas Abonadas (limite 6/ano, 1/mês)
