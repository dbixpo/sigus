# Segurança do Paciente (NSP interno)

Módulo interno do SIGUS para o Núcleo de Segurança do Paciente de cada unidade. **Não substitui o Notivisa** (Anvisa): é o registro da rede municipal, com acompanhamento, encaminhamento e relatório. O número do Notivisa pode ser anotado depois, se a unidade notificar à Anvisa.

Base legal e técnica: RDC 36/2013, Cadernos 6 e 7 da Anvisa, ICPS-OMS, NT GVIMS/GGTES/Anvisa nº 09/2025. A tela de abertura copia o fluxo do MedicSys (Eventos Adversos): notificante, ocorrência, classificação, ação imediata, setor notificado, consulta de protocolo.

## Onde aparece

- Menu **Gestão da Unidade → Segurança do Paciente** (`/sigus/seguranca-paciente/`)
- Aba na ficha da unidade
- **Relatórios → Segurança do Paciente**
- **Configurações → Segurança do Paciente** (listas dos selects)

## Quem usa

A notificação é **da unidade** (não de um chamado de manutenção). O profissional vinculado abre o registro na unidade em que está logado. Gestor central / administrador vê a rede. Permissões na seção `SegurancaPaciente` (Ver, Editar, Adicionar).

Cultura não punitiva: o formulário pede o que aconteceu e o que foi feito na hora, não “quem errou”.

## Protocolo

Formato `SP-AAAA-NNNNN` (ex.: `SP-2026-00001`), único no sistema.

## Listas configuráveis

Tudo que é selectbox vem de `nsp_catalogos`, agrupado em:

| Grupo | Uso |
|--------|-----|
| `status` | Aberto, em análise, encaminhado, plano de ação, concluído, arquivado |
| `classificacao` | Circunstância de risco, quase erro, não conformidade, sem dano, leve, moderado, grave, óbito |
| `tipo_incidente` | Medicação, vacina, queda, falta de sistema/energia/internet, infraestrutura, etc. |
| `tipo_setor` | Administrativo / assistencial |
| `setor` | Recepção, vacina, farmácia… |
| `departamento` | APS, urgência, saúde bucal… |
| `tipo_pessoa` | Paciente, acompanhante, colaborador… |
| `setor_destino` | Destinos de encaminhamento (NSP central, vigilância, farmácia…) |

Dá para incluir, desativar ou marcar “pede texto Outro”, “evento que nunca deveria ocorrer” e “encerra ocorrência”. Itens desativados saem dos formulários novos e permanecem no histórico.

## Encaminhamento

No detalhe, a unidade escala para outro setor (catálogo) e, se fizer sentido, para outra unidade. Gera andamento + notificação no sino para quem está na unidade de destino.

## Investigação

Óbito, dano grave e evento que nunca deveria ocorrer exigem as etapas 5–10 (fatores contribuintes, consequências organizacionais, detecção, atenuantes, melhoria, redução de risco) **antes de encerrar**.

## Busca no SIS

Na nova notificação, CPF, prontuário ou CNS consultam o cadastro no SISWEB (robô `api-consulta-usuario-sis`) e preenchem nome, nascimento, prontuário, CPF e CNS. Credenciais só no `.env` (`SIS_USUARIO`, `SIS_SENHA`, `SIS_CONSULTA_PATH`). Não versionar senha.

## Banco

Ver `migrations/add_nsp.py`. Anexos em `app/static/uploads/nsp/` (até 10 MB; não versionar).

## Atualizar o servidor

Seguir `ATUALIZACAO-SERVIDOR.md` (pull + `pip install -r requirements.txt` + `add_nsp.py` + `add_nsp_sis.py` + `add_nsp_tipos_infra.py` + `.env` SIS + reinício IIS).
