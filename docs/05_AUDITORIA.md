# Módulo de Auditoria

Cada requisição que chega ao SIGUS vira uma linha na tabela `auditoria`, gravada em `after_request` (`app/services/auditoria_http.py`). Se a tela quebrar antes disso, o `teardown_request` grava a mesma linha.

Não entra nesse registro:

- arquivo estático e o `manifest.json` do celular
- a consulta automática do sino (`notificacoes.recentes` e `notificacoes.contagem`), que se repete sozinha o tempo todo
- varredura anônima de endereço inexistente (GET sem rota)

## O que a linha guarda

| Campo | Conteúdo |
|---|---|
| `acao` | Consulta, pesquisa, inclusão, alteração, exclusão, exportação, impressão, login ou saída. O nome no banco continua `view`, `search`, `create`, `update`, `delete`, `export`, `print`, `login`, `logout`. |
| `modulo` | Agenda, apontamentos, mural, veículos, SUEQ, mapa, chamado sem login e os demais blueprints. O filtro da tela lista o que existe no código e o que já apareceu no banco. |
| `endpoint` | Rota Flask, por exemplo `equipamentos.editar`. |
| `entity_id` | Número do registro na URL, quando a rota tem `id`. |
| `parametros` | Campos do formulário, da pesquisa e do JSON. Senha, token, CSRF e foto não são gravados; texto muito longo vira só a contagem de caracteres. |
| `usuario_id`, `ip_address`, `user_agent` | Quem fez, de onde, com qual navegador. |
| `response_status` | Código HTTP da resposta. |

A notificação de Segurança do Paciente (`nsp.notificar`, `nsp.notificado`, `nsp.acompanhar`) entra **sem** usuário, IP, navegador e parâmetros, e a URL fica só com o caminho da rota. É a cultura justa do RI-SGQSP-001: a auditoria não pode ligar a notificação a quem a fez.

## Tela

`/configuracoes/auditoria`, para quem tem Ver em Auditoria na gestão de perfis. O Administrador entra sempre. Dá para filtrar por data, ação, módulo, usuário e endpoint. A coluna Tela mostra a rota e, quando houve formulário ou pesquisa, um resumo dos campos.

Os registros não são alterados nem apagados por essa tela.

`migrations/limpar_auditoria_ruido.py` apaga só o ruído antigo do sino e do manifesto e cria índice em data e módulo. Pode rodar de novo. Não mexe em login, alteração, mural nem frequência.
