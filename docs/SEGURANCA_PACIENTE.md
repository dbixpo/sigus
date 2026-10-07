# Segurança do Paciente (SNI-SGQSP)

Módulo do SIGUS que segue o fluxo do Núcleo de Segurança do Paciente da rede municipal (SNI-SGQSP, regimento RI-SGQSP-001). **Não substitui o Notivisa** (Anvisa): é o registro da rede, com qualificação, investigação, plano de ação e relatório.

Base legal e técnica: RDC 36/2013, Cadernos 6 e 7 da Anvisa, ICPS-OMS, NT GVIMS/GGTES/Anvisa nº 09/2025.

## Fluxo

1. **Qualquer pessoa notifica**, com ou sem login. O nome é opcional; sem nome, a notificação é anônima.
2. A notificação chega **só ao Núcleo**, que qualifica (classificação, grau de dano, criticidade, evento que nunca deveria ocorrer).
3. O Núcleo **encaminha à comissão** de uma ou mais unidades.
4. A comissão **investiga**, monta o plano de ação e comenta.
5. O Núcleo **conclui** ou **arquiva** (arquivar exige motivo) e pode reabrir.

A coordenação da unidade só vê o caso se o Núcleo **liberar o acesso** naquele encaminhamento. Administrador e Gestor Central **não veem casos** por causa do perfil: só quem está no Núcleo ou na comissão.

Etapas: Em qualificação → Qualificada → Encaminhada → Em investigação → Concluída (ou Arquivada).

Evento sentinela, dano grave ou óbito, criticidade crítica e evento que nunca deveria ocorrer **exigem investigação concluída** antes de encerrar.

## Cultura justa (anonimato)

A notificação nunca fica ligada a quem a fez:

- `criado_por` fica sempre vazio, mesmo com o usuário logado.
- A auditoria grava as rotas `nsp.notificar`, `nsp.notificado` e `nsp.acompanhar` **sem usuário, IP e navegador** (`_ENDPOINTS_ANONIMOS` em `app/__init__.py`).
- O nome e o cargo do notificante, quando informados, aparecem só para o Núcleo.

O notificante **não identifica o paciente**: informa um código e a faixa etária. O formulário recusa algo que pareça CPF, CNS ou prontuário. Quem identifica o paciente depois é o Núcleo, na aba Paciente, com busca no SIS.

## Quem é quem

| Papel | Como entra | O que faz |
|---|---|---|
| Núcleo | Lista em **Configurações → Segurança do Paciente** (`nsp_membros`, papel `nucleo`) | Vê tudo; qualifica, encaminha, libera a coordenação, identifica o paciente, conclui |
| Comissão | Mesma lista, papel `comissao` + unidade | Vê os casos encaminhados à sua unidade; investiga, plano de ação, comentários, anexos |
| Coordenação | Gestor principal/secundário da unidade, ou perfil Gestor de Área vinculado | Só leitura, e só dos casos liberados pelo Núcleo |

O pertencimento ao Núcleo é por lista, independente do perfil do usuário. Quem gerencia a lista: administrador ou membro do Núcleo (`/seguranca-paciente/membros`).

## Telas

| URL (prefixo `/sigus`) | Login | Uso |
|---|---|---|
| `/seguranca-paciente/notificar` | Não | Formulário de notificação (link público e QR code) |
| `/seguranca-paciente/notificado/<protocolo>` | Não | Comprovante com o protocolo |
| `/seguranca-paciente/acompanhar?protocolo=…` | Não | Mostra só a etapa e a data de recebimento, sem conteúdo do caso |
| `/seguranca-paciente/` | Sim | Painel do Núcleo / comissão |
| `/seguranca-paciente/<id>` | Sim | Detalhe em abas: qualificação, paciente, encaminhamento, investigação, plano, histórico |
| `/seguranca-paciente/relatorios` | Sim | Indicadores e painel na mesma página; exporta Excel e CSV |
| `/seguranca-paciente/membros` | Sim | Núcleo e comissões |

O menu **Operações → Segurança do Paciente** aparece para todos (todos podem notificar). O painel só mostra casos conforme o papel acima.

## Protocolo

Formato `SP-AAAA-XXXXXX`, com 6 caracteres aleatórios (sem letras e números ambíguos). Não é sequencial, para não revelar volume nem permitir adivinhar o protocolo de outra pessoa.

## Busca no SIS

Na aba Paciente, o Núcleo consulta CPF, prontuário ou CNS no SISWEB (robô `api-consulta-usuario-sis`) e preenche nome, nascimento, prontuário, CPF e CNS. Credenciais só no `.env` (`SIS_USUARIO`, `SIS_SENHA`, `SIS_CONSULTA_PATH`). Não versionar senha.

## Banco

- `migrations/add_nsp.py`, `add_nsp_sis.py`, `add_nsp_tipos_infra.py`: tabelas originais.
- `migrations/add_nsp_fluxo_nucleo.py`: etapas, qualificação, investigação, plano de ação (`nsp_acoes`), membros (`nsp_membros`) e liberação da coordenação. Idempotente.
- Anexos em `app/static/uploads/nsp/` (até 10 MB; não versionar).
- Os catálogos antigos (`nsp_catalogos`) ficam só para leitura do histórico; o formulário novo usa as listas fixas de `app/models/nsp.py` (tipologia, turno, faixa etária, classificação, dano, criticidade, metodologia).

## Atualizar o servidor

Seguir [ATUALIZACAO-SERVIDOR.md](../ATUALIZACAO-SERVIDOR.md): rodar `add_nsp_fluxo_nucleo.py` e reiniciar **só o processo do SIGUS** (em Sorocaba, nunca o IIS). Depois, cadastrar os membros do Núcleo em **Configurações → Segurança do Paciente**: sem ninguém na lista, as notificações chegam mas ninguém as vê.

Manual da ponta: livro na Estante SES ([MANUAIS_ESTANTE.md](MANUAIS_ESTANTE.md)).
