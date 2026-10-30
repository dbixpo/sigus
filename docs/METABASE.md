# Metabase no SIGUS

Painéis do Metabase aparecem dentro do SIGUS, no menu da esquerda. A pessoa vê só o que foi liberado para o perfil dela, o tipo da unidade em que ela está e o CBO (cadastro ou da unidade).

A chave de incorporação fica no banco e, se quiser, no `.env` da máquina. Ela não entra no Git. O navegador recebe um token assinado que vale 10 anos. O relógio do Metabase está horas à frente deste computador: com 10 minutos o token já nascia vencido (`Token is expired`).

## O que a pessoa vê

Menu **Metabase**, com o ícone do Metabase.

Do lado direito do painel:

- **Pedir acesso ao Metabase.** Abre um modal só com a justificativa. O SIGUS grava um chamado administrativo para a unidade Saúde Digital, com nome, CPF, e-mail, perfil em uso no SIGUS, CBO de cadastro, CBO na unidade, unidade e tipo de unidade. A matriz GUT vai como 3, 3 e 3 (prioridade média), porque esse botão não pede GUT. Se já existir um pedido em aberto da mesma pessoa, o sistema não abre outro.
- **Play.** Troca os painéis sozinho. O tempo padrão é 40 segundos e se muda em Configurações → Metabase, antes da lista de painéis. Pausar devolve o botão para play e abre o bloco para passar na mão (anterior, próximo e a lista).
- **Tela cheia.** A apresentação continua trocando sozinha. Pausar dentro da tela cheia também libera a passagem manual. No celular, se o aparelho não deixar a tela cheia de verdade, o painel cobre a tela do mesmo jeito.
- **Celular.** O título fica em cima e os botões embaixo: pedir acesso vira só o ícone da chave, com área de toque maior. O gráfico ocupa o que sobra. No computador o título e os botões continuam na mesma linha.
- **Barra dos painéis.** Os publicados ficam numa linha só. Se não couberem, a barra rola na horizontal, no celular e no computador.

No gráfico incorporado dá para clicar e abrir o registro, do mesmo jeito que no Metabase.

## Configuração

Configurações → **Metabase**. Quem mexe é Administrador e, na matriz nova, Gestor Central (Editar e Adicionar). Os outros perfis só veem o menu.

Na conexão:

- URL do site, em https, por exemplo `https://saudedigital.sorocaba.sp.gov.br/metabase` (o SIGUS de produção é https; painel em http o navegador bloqueia)
- chave secreta de incorporação (a mesma configurada no Metabase)
- segundos da apresentação (10 a 600)

Cada painel tem nome, número do dashboard (o `580` de `/dashboard/580`), título, ativo, perfis, tipos de unidade e CBOs. O download do gráfico fica desligado. Lista vazia em tipo de unidade ou CBO significa todo mundo. Arrastar a linha grava a ordem da apresentação.

No painel, cole o Python que o Metabase gera (`import jwt`, `payload` com `resource`, `params` e `exp`). A linha `exp: round(time.time()) + (60 * 10) # 10 minute expiration` fica como veio: o SIGUS assina por 10 anos. A chave que vier nesse texto não é gravada no painel.

O IIS na frente do Metabase recusa um pedaço de endereço maior que 260 caracteres e devolve `Bad Request - Invalid URL`. O token vai nesse pedaço. O Python do exemplo, sem `_embedding_params`, gera um token de cerca de 160 caracteres e abre. Com os filtros em português dentro do token, ele passa de 500 e o IIS barra.

O dashboard **580** já entra nesta instalação, visível para todos os perfis, tipos e categorias, com borda e título. Dá para renomear e restringir.

## Permissão

Seção **Metabase** em Gestão de Perfis (`OUT_Metabase`):

- Ver: abre o menu
- Editar e Adicionar: a tela de configuração

## Produção

Depois do `git pull`, com backup do banco:

```powershell
.\venv\Scripts\python.exe -m pip install PyJWT==2.10.1
.\venv\Scripts\python.exe migrations\add_metabase.py
.\venv\Scripts\python.exe migrations\seed_permissoes_faltantes.py
```

Os dois scripts de banco são idempotentes. O de permissão só cria a linha que ainda não existe.

A chave: ou `METABASE_SECRET_KEY` no `.env` **daquela** máquina antes de rodar `add_metabase.py` (ele só preenche se o banco estiver vazio), ou colar em Configurações → Metabase depois. Não commitar o `.env`. O `database/sigus_inicial.sql` deixa essa chave vazia.

Reinicie só o processo do SIGUS. Não use `iisreset` se o IIS atende outro site.

Conferência: menu Metabase abre o dashboard 580; play troca no tempo configurado; pausar mostra a lista; tela cheia mantém a troca; pedir acesso gera um chamado `CA…` na fila da Saúde Digital com os dados da pessoa.
