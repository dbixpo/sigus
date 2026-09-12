# -*- coding: utf-8 -*-
"""Publica o manual de utilização do SIGUS na Estante SES (BookStack).

Credenciais só por variável de ambiente. Não versionar senha.
  ESTANTE_EMAIL  ESTANTE_SENHA
"""
from __future__ import annotations

import os
import sys

import requests
from bs4 import BeautifulSoup

BASE = 'https://estante-ses.sorocaba.sp.gov.br'
BOOK_ID = 45
SIGUS_URL = 'https://saudedigital.sorocaba.sp.gov.br/sigus'


def c(kind: str, titulo: str, texto: str) -> str:
    return f'<p class="callout {kind}"><strong>{titulo}</strong> {texto}</p>'


def session_login() -> requests.Session:
    email = (os.environ.get('ESTANTE_EMAIL') or '').strip()
    senha = os.environ.get('ESTANTE_SENHA') or ''
    if not email or not senha:
        sys.exit('Defina ESTANTE_EMAIL e ESTANTE_SENHA no ambiente.')
    s = requests.Session()
    s.headers['User-Agent'] = 'SIGUS-manual-estante'
    r = s.get(f'{BASE}/login', timeout=40)
    r.raise_for_status()
    token = BeautifulSoup(r.text, 'html.parser').find('input', {'name': '_token'})
    if not token or not token.get('value'):
        sys.exit('Não achei o token de login da Estante.')
    r2 = s.post(
        f'{BASE}/login',
        data={'_token': token['value'], 'email': email, 'password': senha},
        timeout=40,
        allow_redirects=True,
    )
    if '/login' in r2.url and 'logout' not in r2.text.lower():
        sys.exit('Login na Estante falhou.')
    return s


def api(s: requests.Session, method: str, path: str, **kw):
    r = s.request(method, f'{BASE}/api{path}', timeout=60, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f'{method} {path} -> {r.status_code}: {r.text[:800]}')
    return r.json() if r.content else {}


BOOK_DESC = (
    '<p>Aqui você encontra os manuais operacionais do <strong>SIGUS</strong> — '
    'Sistema Integrado de Gestão das Unidades de Saúde da Secretaria da Saúde de Sorocaba.</p>'
    '<p>O SIGUS é a ferramenta da Saúde Digital para a gestão da unidade: patrimônio, '
    'chamados, planejamentos, agenda, segurança do paciente, pessoas e contratos. '
    'Ele <strong>não substitui o SISWEB</strong> (prontuário e atendimento). Os dois sistemas se complementam.</p>'
    f'<p>Acesso: <a href="{SIGUS_URL}">{SIGUS_URL}</a></p>'
    + c('info', 'Como usar este livro:',
        'Comece por “O que é o SIGUS” e “Como entrar”. Depois abra o capítulo da rotina que você faz no dia a dia. '
        'O menu do sistema só mostra o que o seu perfil pode ver — se um item não aparecer, não é falta do sistema: é permissão.')
)

CHAPTERS = [
    {
        'name': 'Começando a usar o SIGUS',
        'description': 'O que é o sistema, como entrar, unidade de trabalho, senha e o que cada perfil enxerga.',
        'pages': [
            {
                'name': 'O que é o SIGUS',
                'html': f'''
<p>O <strong>SIGUS</strong> (Sistema Integrado de Gestão das Unidades de Saúde) é o sistema da Saúde Digital para organizar o dia a dia das unidades da rede municipal de Sorocaba: o prédio, as salas, os equipamentos, os chamados de manutenção, os planejamentos, a agenda, as pessoas e a segurança do paciente.</p>
<p>Pense nele como a “gestão da casa”. O atendimento clínico do cidadão continua no <strong>SISWEB</strong>. O SIGUS cuida do que faz a unidade funcionar.</p>
<h2>O que você encontra no sistema</h2>
<table>
<thead><tr><th>Área do menu</th><th>Para que serve</th></tr></thead>
<tbody>
<tr><td>Dashboard</td><td>Visão inicial depois do login.</td></tr>
<tr><td>Gestão da Unidade</td><td>Ficha da unidade, planejamentos, agenda, segurança do paciente, links úteis e relatórios.</td></tr>
<tr><td>Recursos Humanos</td><td>Faltas abonadas e cadastro público de vínculo.</td></tr>
<tr><td>Operações</td><td>Fila de gestão de chamados e transferências de equipamentos.</td></tr>
<tr><td>Gestão Financeira</td><td>Contratos, empenho, empresas, emendas e licitações (quem tiver permissão).</td></tr>
<tr><td>Configurações</td><td>Perfis, usuários, feriados, auditoria e listas do sistema (administrador e quem for autorizado).</td></tr>
</tbody>
</table>
{c('info', 'Endereço de acesso:', f'Abra o navegador e entre em <a href="{SIGUS_URL}">{SIGUS_URL}</a>. Prefira um navegador atualizado (Edge, Chrome ou Firefox).')}
{c('warning', 'ATENÇÃO:', 'O SIGUS não é prontuário. Não registre consulta, SOAP, vacina ou guia de encaminhamento aqui. Isso continua no SISWEB.')}
<h2>Quem usa</h2>
<p>Qualquer profissional vinculado a uma unidade pode usar o SIGUS, no limite do perfil. Os nomes que o sistema usa:</p>
<table>
<thead><tr><th>Perfil</th><th>Em geral</th></tr></thead>
<tbody>
<tr><td>Operador padrão</td><td>Rotina da unidade: chamados, agenda, notificações de segurança do paciente, faltas abonadas.</td></tr>
<tr><td>Apoio administrativo</td><td>Cadastros da unidade, equipamentos, chamados e apoio à gestão.</td></tr>
<tr><td>Gestor de área</td><td>Unidades vinculadas, planejamentos e acompanhamento.</td></tr>
<tr><td>Gestor central</td><td>Visão da rede, relatórios, contratos.</td></tr>
<tr><td>Administrador</td><td>Tudo, inclusive configurações, usuários e auditoria.</td></tr>
</tbody>
</table>
{c('success', 'Dica:', 'Se um botão ou menu não aparece para você, peça à coordenação para conferir o perfil e o vínculo com a unidade. Não compartilhe login com colega: cada registro fica no seu nome.')}
'''
            },
            {
                'name': 'Como entrar no sistema',
                'html': f'''
<p>Neste capítulo você aprende a abrir o SIGUS, informar o e-mail, a senha e conferir se está na unidade certa.</p>
<h2>Passo a passo do login</h2>
<ol>
<li>Acesse <a href="{SIGUS_URL}">{SIGUS_URL}</a>.</li>
<li>No campo <strong>E-mail</strong>, digite seu usuário. Pode ser o endereço completo (<em>nome@sorocaba.sp.gov.br</em>) ou só a parte antes do @ — o sistema completa o domínio da Prefeitura.</li>
<li>Digite sua <strong>senha</strong>. O ícone do olho mostra ou esconde o que você digitou.</li>
<li>Se estiver no seu computador de trabalho, pode marcar <strong>Lembrar-me</strong>.</li>
<li>Clique em <strong>Entrar</strong>.</li>
</ol>
{c('info', 'Campos com *:', 'No SIGUS, o que é obrigatório vem marcado com asterisco. O sistema não deixa seguir se faltar dado essencial.')}
<h2>Não consegui entrar</h2>
<ul>
<li>Confira se o e-mail está certo e se o teclado não está em maiúsculas (Caps Lock).</li>
<li>Se a senha foi redefinida recentemente, use a nova senha — a antiga deixa de valer.</li>
<li>Se a tela disser que o usuário está inativo, a coordenação ou a Saúde Digital precisa reativar o cadastro.</li>
</ul>
{c('warning', 'ATENÇÃO:', 'O login é pessoal e intransferível. Tudo o que você registra (chamado, notificação, falta abonada) fica auditado no seu usuário.')}
<h2>Primeiro acesso e vínculo com a unidade</h2>
<p>Quem não é administrador nem gestor central precisa estar <strong>vinculado a pelo menos uma unidade ativa</strong>. Sem esse vínculo, o menu da gestão da unidade não abre de verdade: o sistema espera que a coordenação aprove o seu cadastro.</p>
<p>Profissionais novos podem se cadastrar pelo formulário público de vínculo (há um item de <strong>Cadastro Público</strong> no menu de Recursos Humanos, para quem pode divulgá-lo). A coordenação ou o apoio administrativo da unidade vê o pedido na ficha da unidade, na aba de solicitações, e aprova ou recusa.</p>
{c('success', 'Dica:', 'Se você mudou de unidade, peça o novo vínculo. Continuar logado na unidade antiga faz chamados e notificações nascerem no lugar errado.')}
'''
            },
            {
                'name': 'Unidade de trabalho, perfil e senha',
                'html': '''
<p>Depois de entrar, o SIGUS precisa saber <strong>em qual unidade você está trabalhando agora</strong>. Isso vale especialmente se você atua em mais de um serviço.</p>
<h2>Unidade padrão</h2>
<p>No topo da tela há o seletor de unidade. A unidade escolhida vira o contexto de:</p>
<ul>
<li>abertura de chamados;</li>
<li>notificações de segurança do paciente;</li>
<li>agenda e planejamentos;</li>
<li>o atalho da unidade no menu lateral.</li>
</ul>
<ol>
<li>Abra a lista de unidades no topo.</li>
<li>Escolha a unidade do plantão ou do expediente de hoje.</li>
<li>Confirme. O sistema grava essa escolha como unidade padrão.</li>
</ol>
<p class="callout warning"><strong>IMPORTANTE:</strong> Administrador e gestor central enxergam a rede. Mesmo assim, ao registrar algo “da unidade”, confira o seletor — o registro nasce na unidade escolhida, não “na Secretaria inteira”.</p>
<h2>Meu perfil</h2>
<p>No canto superior direito, abra o seu nome e clique em <strong>Meu Perfil</strong>. Lá você:</p>
<ul>
<li>confere nome, e-mail e foto;</li>
<li>altera a senha (senha atual + nova senha duas vezes);</li>
<li>vê unidades às quais está vinculado.</li>
</ul>
<h2>Sino de notificações</h2>
<p>O sino no topo avisa quando chega encaminhamento, andamento de chamado, pedido de vínculo ou mensagem da segurança do paciente. Clique para ler e, se quiser, marque todas como lidas.</p>
<h2>O menu muda de pessoa para pessoa</h2>
<p>O SIGUS não esconde funções “por capricho”. Cada perfil tem permissões de <strong>Ver</strong>, <strong>Editar</strong> e <strong>Adicionar</strong> por seção (unidades, chamados, segurança do paciente, etc.). Quem administra isso é a tela <strong>Configurações → Gestão de Perfis</strong>.</p>
<p class="callout info"><strong>Dica:</strong> Use a busca do menu lateral (“Buscar no menu…”) quando não lembrar o nome da tela. Se nada aparecer, a função não está liberada para o seu perfil.</p>
'''
            },
        ],
    },
    {
        'name': 'A ficha da sua unidade',
        'description': 'Salas, equipamentos, profissionais, chamados e as abas do dia a dia.',
        'pages': [
            {
                'name': 'Como abrir a ficha da unidade',
                'html': '''
<p>A ficha da unidade é a “capa” do serviço no SIGUS. Quase tudo que é da casa passa por ela.</p>
<h2>Como chegar</h2>
<ol>
<li>Confira a unidade padrão no topo.</li>
<li>No menu <strong>Gestão da Unidade</strong>, clique no nome da unidade (ou em <strong>Unidades</strong>, se você vê a lista da rede).</li>
<li>A ficha abre com várias abas.</li>
</ol>
<h2>O que tem em cada aba</h2>
<table>
<thead><tr><th>Aba</th><th>O que você faz</th></tr></thead>
<tbody>
<tr><td>Chamados</td><td>Vê os chamados abertos da unidade e abre um novo.</td></tr>
<tr><td>Segurança do Paciente</td><td>Vê as notificações recentes do NSP da unidade e abre uma nova.</td></tr>
<tr><td>Equipamentos</td><td>Inventário por sala (computador, maca, ar-condicionado…).</td></tr>
<tr><td>Salas</td><td>Consultório, farmácia, vacina, recepção etc.</td></tr>
<tr><td>Profissionais</td><td>Quem está vinculado e ativo na unidade.</td></tr>
<tr><td>Fichas CNES</td><td>Fichas e vínculos usados no cadastro junto ao CNES.</td></tr>
<tr><td>Solicitações</td><td>Pedidos de vínculo de profissionais novos, para aprovar ou recusar.</td></tr>
<tr><td>Informações</td><td>Endereço, telefone, tipo de unidade e dados cadastrais.</td></tr>
</tbody>
</table>
<p class="callout info"><strong>Dica:</strong> Equipamento sem sala certa vira chamado e transferência confusos. Mantenha a aba de salas e a de equipamentos alinhadas com o que existe de verdade no prédio.</p>
<h2>Impressos do SIGUS</h2>
<p>Várias telas têm o botão <strong>Imprimir</strong>. No SIGUS o padrão é abrir um <strong>quadro (modal)</strong> com a pré-visualização do documento institucional (logo da Prefeitura, Secretaria da Saúde, campos e espaço para assinatura). De lá você escolhe <strong>Imprimir / Salvar PDF</strong>.</p>
<p class="callout success"><strong>Vale para:</strong> chamado, segurança do paciente, falta abonada, termo de transferência, planejamento e contrato — o visual é o mesmo padrão da casa.</p>
'''
            },
            {
                'name': 'Como abrir e acompanhar um chamado',
                'html': '''
<p>Chamado no SIGUS é pedido de manutenção ou de equipamento da unidade — não é notificação de incidente clínico (isso é Segurança do Paciente) e não é atendimento do cidadão (isso é SISWEB).</p>
<h2>Quando abrir</h2>
<ul>
<li>Algo quebrou ou parou de funcionar (ar-condicionado, computador, maca, fechadura).</li>
<li>Há problema no prédio (infiltração, elétrica, hidráulica, acessibilidade).</li>
<li>A unidade precisa de um equipamento novo ou de substituição.</li>
</ul>
<h2>Passo a passo</h2>
<ol>
<li>Na ficha da unidade, aba <strong>Chamados</strong>, clique para abrir um novo — ou use o fluxo de novo chamado do módulo.</li>
<li>Escolha o tipo:
<ul>
<li><strong>Bem permanente</strong> — item que já existe no inventário (computador, maca, geladeira).</li>
<li><strong>Solicitação de equipamento</strong> — necessidade de item novo ou substituição, informando a sala e o motivo.</li>
<li><strong>Predial</strong> — problema do prédio / infraestrutura.</li>
</ul>
</li>
<li>Preencha a descrição com o máximo de detalhe útil (o que acontece, desde quando, o que já tentaram).</li>
<li>Anexe foto ou vídeo, se ajudar o técnico (há limite de tamanho por arquivo).</li>
<li>Envie. O sistema gera um <strong>número de chamado</strong>.</li>
</ol>
<p class="callout warning"><strong>ATENÇÃO:</strong> Se o chamado é de um bem permanente, escolha o equipamento certo na lista. Chamado “solto”, sem patrimônio, atrasa o atendimento e confunde a transferência depois.</p>
<h2>Acompanhar</h2>
<p>Na mesma aba você vê status, prioridade e última atualização. Abrindo o chamado, há a linha do tempo (andamentos) e o botão de impressão no padrão SIGUS.</p>
<p>Quem trabalha no setor de manutenção usa a tela <strong>Operações → Gestão de Chamados</strong> (fila da unidade que recebe o serviço), não só a aba da unidade solicitante.</p>
<p class="callout info"><strong>Dica:</strong> O impresso do chamado traz identificação da unidade, local ou equipamento, descrição e histórico. Use-o quando precisar protocolar no físico ou enviar a um prestador.</p>
'''
            },
        ],
    },
    {
        'name': 'Segurança do Paciente',
        'description': 'Notificação interna do NSP da unidade: protocolo, SIS, investigação e impresso.',
        'pages': [
            {
                'name': 'O que é a Segurança do Paciente no SIGUS',
                'html': '''
<p>O módulo <strong>Segurança do Paciente</strong> é o registro interno do <strong>Núcleo de Segurança do Paciente (NSP)</strong> da unidade. Serve para aprender com o que aconteceu e melhorar o cuidado — não para punir pessoas.</p>
<p>Base: RDC 36/2013, classificação da OMS (ICPS) e orientações da Anvisa. O SIGUS <strong>não envia nada para o Notivisa</strong>. Se a unidade notificar a Anvisa, você só anota o número e a data no registro.</p>
<h2>O que deve ser notificado</h2>
<ul>
<li>Circunstância de risco (algo inseguro, mesmo sem erro).</li>
<li>Quase erro (o incidente foi detido antes de atingir a pessoa).</li>
<li>Incidente sem dano, dano leve, moderado, grave ou óbito.</li>
<li>Não conformidade.</li>
<li>Evento que nunca deveria ocorrer (o sistema chama de “jamais deveria ocorrer”).</li>
</ul>
<p class="callout info"><strong>Protocolo:</strong> cada notificação ganha um número no formato <strong>SP-AAAA-NNNNN</strong>, por exemplo SP-2026-00001. Guarde esse número para consultar depois.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> Óbito, dano grave e evento que nunca deveria ocorrer <strong>não podem ser encerrados</strong> sem a investigação completa (etapas 5 a 10 da Anvisa) no próprio registro.</p>
<h2>Quem vê</h2>
<p>A notificação é da <strong>unidade</strong>, não de um chamado de manutenção. Profissional com permissão de ver/adicionar registra na unidade em que está logado. Gestor central e administrador veem a rede. As listas dos selects (tipos de incidente, setores, destinos) ficam em <strong>Configurações → Segurança do Paciente</strong>.</p>
'''
            },
            {
                'name': 'Como abrir uma notificação',
                'html': '''
<p>Menu <strong>Gestão da Unidade → Segurança do Paciente → Nova notificação</strong> (ou o botão na aba da ficha da unidade).</p>
<h2>1. Quem notifica e onde aconteceu</h2>
<p>Confira a unidade. Informe o nome de quem está notificando, o tipo de setor (administrativo ou assistencial) e o setor. Se a lista não tiver o setor, use <strong>Outro</strong> e descreva.</p>
<h2>2. Pessoa afetada</h2>
<ol>
<li>Selecione o <strong>tipo de pessoa</strong>: paciente, acompanhante, colaborador, visitante ou outros.</li>
<li>Se <strong>não for paciente</strong>, preencha nome e, se souber, nascimento. Não pede busca no SIS.</li>
<li>Se <strong>for paciente</strong>, escolha como identificar: <strong>CPF</strong>, <strong>CNS</strong> ou <strong>prontuário</strong>.</li>
<li>Digite só aquele dado e clique em <strong>Buscar no SIS</strong>. O sistema consulta o cadastro e preenche nome, nascimento, prontuário, CPF e CNS.</li>
<li>Se o SIS não encontrar (ou a consulta falhar), clique em <strong>Não achei / preencher na mão</strong> e registre mesmo assim. O identificador que você digitou já entra no campo correspondente.</li>
</ol>
<p class="callout warning"><strong>ATENÇÃO:</strong> A busca usa exatamente o critério que você marcou. Não adivinha pelo tamanho do número. CPF tem 11 dígitos; CNS, 15.</p>
<p class="callout success"><strong>Dica:</strong> Sempre confira o nome que voltou do SIS antes de enviar. Dado importado não significa dado conferido.</p>
<h2>3. Ocorrência</h2>
<ul>
<li>Data e hora do fato (não a data em que você está registrando).</li>
<li>Tipo de incidente (medicação, queda, identificação, <strong>falta de sistema, energia ou internet</strong>, infraestrutura, recursos etc.).</li>
<li>Classificação (circunstância de risco, quase erro, sem dano, leve, moderado, grave, óbito…).</li>
<li>Descrição do que aconteceu, em linguagem factual — o que se viu, não “quem é o culpado”.</li>
<li>Ação imediata: o que foi feito na hora para proteger a pessoa e conter o risco.</li>
</ul>
<h2>4. Enviar</h2>
<p>Ao registrar, o SIGUS gera o protocolo e abre a ficha da notificação. Dali você imprime (modal padrão), anexa evidência, comenta, encaminha a outro setor e preenche a investigação.</p>
<p class="callout info"><strong>Cultura não punitiva:</strong> descreva o processo. Nomes de profissionais só quando forem necessários para o cuidado ou para o encaminhamento, nunca para expor.</p>
'''
            },
            {
                'name': 'Acompanhar, investigar, encaminhar e imprimir',
                'html': '''
<p>Abra a notificação pelo protocolo na lista, pela consulta de protocolo ou pela aba da unidade.</p>
<h2>Status</h2>
<p>Quem edita pode mudar: aberto, em análise, encaminhado, plano de ação, concluído, arquivado. Encerrar sem investigação, nos casos graves, o sistema bloqueia.</p>
<h2>Investigação (etapas 5 a 10 da Anvisa)</h2>
<ol>
<li>Fatores contribuintes</li>
<li>Consequências organizacionais</li>
<li>Detecção</li>
<li>Fatores atenuantes do dano</li>
<li>Ações de melhoria</li>
<li>Ações para reduzir o risco</li>
</ol>
<p>Há também um resumo da análise e a marcação de <strong>evento que nunca deveria ocorrer</strong>, se ainda não estiver marcada.</p>
<h2>Notivisa</h2>
<p>Se a unidade já notificou a Anvisa, marque e informe número e data. O SIGUS só guarda a informação — não transmite.</p>
<h2>Plano de ação e encaminhamento</h2>
<p>Inclua ações com responsável e prazo. Encaminhe a outro destino do catálogo (NSP da unidade, coordenação, NSP central, vigilância, farmácia, diretoria, vigilância sanitária…). Se fizer sentido, escolha outra unidade. Quem está no destino recebe aviso no sino.</p>
<h2>Imprimir</h2>
<p>O botão <strong>Imprimir</strong> abre o modal do SIGUS com o documento institucional: protocolo, classificação, pessoa afetada, descrição, ação imediata, investigação, plano, linha do tempo e espaço para assinatura do notificante, do NSP e do responsável da unidade. Se houver foto anexa, ela vai para a página seguinte do impresso.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> O impresso contém dado de paciente. Não deixe cópia em local de circulação nem envie por canal inseguro.</p>
<h2>Relatórios</h2>
<p>Em <strong>Relatórios → Segurança do Paciente</strong> você filtra a rede (ou suas unidades), vê totais e exporta planilha. Útil para o NSP acompanhar volume, gravidade e tipos de incidente.</p>
'''
            },
        ],
    },
    {
        'name': 'Planejamentos e agenda',
        'description': 'Projetos da unidade, prazos, reuniões e feriados.',
        'pages': [
            {
                'name': 'Planejamentos da unidade',
                'html': '''
<p>O módulo de <strong>Planejamentos</strong> organiza projetos e ações da unidade em formato de quadro (colunas de status), com priorização.</p>
<h2>Para que serve</h2>
<p>Combinar o que a equipe vai fazer, quem é responsável, até quando, e acompanhar o andamento sem perder o combinado em planilha solta.</p>
<ol>
<li>Menu <strong>Gestão da Unidade → Planejamentos</strong>.</li>
<li>Abra ou crie um plano (projeto) vinculado à unidade.</li>
<li>Inclua ações. O status da ação anda no quadro conforme o trabalho avança.</li>
<li>Use a impressão do projeto ou do resumo (abertos, concluídos, cancelados) pelo modal padrão do SIGUS.</li>
</ol>
<p class="callout info"><strong>GUT:</strong> alguns planos usam gravidade, urgência e tendência para priorizar. Quanto maior o produto desses fatores, mais o item sobe na fila de atenção.</p>
<p class="callout success"><strong>Dica:</strong> Prazos de planejamento também podem aparecer na <strong>Agenda</strong> da unidade. Assim o combinado do plano não fica só no quadro.</p>
'''
            },
            {
                'name': 'Agenda da unidade',
                'html': '''
<p>A <strong>Agenda</strong> junta, no mesmo calendário:</p>
<ul>
<li>compromissos e eventos da unidade;</li>
<li>reuniões (com lista de participantes, quando for o caso);</li>
<li>prazos de planejamentos;</li>
<li>feriados cadastrados pela administração (com expediente especial, se houver).</li>
</ul>
<h2>Como usar</h2>
<ol>
<li>Menu <strong>Gestão da Unidade → Agenda</strong>.</li>
<li>Navegue por dia, semana ou mês.</li>
<li>Clique em um horário vazio para criar evento, ou abra um evento existente para editar (se você puder editar).</li>
<li>Marque se é reunião quando precisar registrar participantes.</li>
</ol>
<p class="callout info"><strong>Feriados:</strong> quem tem permissão em Configurações cadastra feriados municipais e o expediente do dia. Na agenda eles aparecem destacados para ninguém marcar atividade numa data sem funcionamento.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> A agenda do SIGUS é da <strong>unidade</strong>, não substitui a agenda de consultas do SISWEB.</p>
'''
            },
        ],
    },
    {
        'name': 'Operações: fila de chamados e transferências',
        'description': 'Quem recebe manutenção e quem troca equipamento entre unidades.',
        'pages': [
            {
                'name': 'Gestão de chamados',
                'html': '''
<p>A tela <strong>Operações → Gestão de Chamados</strong> é a fila de quem <strong>executa</strong> o serviço (manutenção da unidade que trata aquele tipo de chamado), não a lista de quem só abriu o pedido.</p>
<h2>O que você vê</h2>
<ul>
<li>Totais por status.</li>
<li>Filtros de setor, status e busca.</li>
<li>Ações rápidas: atualizar status e imprimir.</li>
</ul>
<p>Abra o chamado para registrar andamento, anexar evidência, encaminhar e encerrar com observação de conclusão.</p>
<p class="callout warning"><strong>IMPORTANTE:</strong> Só unidades configuradas para receber determinados tipos de chamado entram nessa fila. Se o seu serviço não aparece, a unidade ainda não está marcada como prestadora daquele tipo — isso se ajusta no cadastro da unidade / configurações, não “forçando” o chamado.</p>
'''
            },
            {
                'name': 'Transferência de equipamentos',
                'html': '''
<p>Quando um bem permanente precisa mudar de unidade (ou de local), use <strong>Operações → Transferências</strong>. Não “apague” o equipamento de uma lista e cadastre de novo na outra: o histórico patrimonial se perde.</p>
<ol>
<li>Localize o equipamento na ficha da unidade de origem.</li>
<li>Solicite a transferência, informando o destino e o motivo.</li>
<li>A unidade de destino <strong>aceita</strong> (ou recusa) o termo.</li>
<li>Imprima o termo de transferência pelo modal padrão do SIGUS e colete as assinaturas.</li>
</ol>
<p class="callout info"><strong>Dica:</strong> Conferir número de patrimônio e sala antes de enviar evita aceite de item errado.</p>
'''
            },
        ],
    },
    {
        'name': 'Pessoas: faltas abonadas e vínculo',
        'description': 'Direito das seis faltas abonadas e entrada de profissional na unidade.',
        'pages': [
            {
                'name': 'Faltas abonadas',
                'html': '''
<p>Servidores estatutários têm direito a <strong>6 faltas abonadas no ano</strong>, no máximo <strong>1 por mês</strong>. O SIGUS controla esse limite para o seu usuário.</p>
<h2>Como registrar</h2>
<ol>
<li>Menu <strong>Recursos Humanos → Faltas Abonadas</strong>.</li>
<li>Escolha a data (o calendário já bloqueia mês em que você já usou abonada ativa).</li>
<li>Informe função e unidade, se o sistema pedir.</li>
<li>Salve e imprima o documento pelo modal (padrão institucional, para a chefia).</li>
</ol>
<p class="callout warning"><strong>ATENÇÃO:</strong> A abonada deve ser combinada com a chefia com antecedência (regra da casa: em geral 2 dias úteis). O SIGUS registra o pedido; a autorização da escala continua sendo da chefia. Cargo de confiança segue a legislação específica — nem todo mundo acumula abonada para pagamento.</p>
<p>Abonadas canceladas não contam no limite do ano e aparecem no histórico. Quem gerencia usuários pode ver a ficha de outra pessoa; o operador padrão vê a própria.</p>
'''
            },
            {
                'name': 'Cadastro público e vínculo na unidade',
                'html': '''
<p>Profissional que ainda não tem usuário no SIGUS pode pedir vínculo pelo formulário público (<strong>solicitar vínculo profissional</strong>). Não precisa estar logado.</p>
<h2>Quem pede</h2>
<ol>
<li>Abre o link divulgado pela unidade.</li>
<li>Preenche dados pessoais, CPF válido, CBO, tipo de vínculo e a unidade desejada.</li>
<li>Envia. O pedido fica <strong>pendente</strong>.</li>
</ol>
<h2>Quem aprova</h2>
<p>Na ficha da unidade, aba <strong>Solicitações</strong>, a coordenação ou o apoio administrativo (e os perfis centrais) vê o pedido, aprova ou recusa. Na aprovação o SIGUS:</p>
<ul>
<li>cria o usuário (perfil operador padrão), se ainda não existir;</li>
<li>vincula à unidade;</li>
<li>registra a ficha CNES do vínculo.</li>
</ul>
<p class="callout info"><strong>Sino:</strong> gestores da unidade recebem notificação de pedido novo. Não deixe a aba de solicitações acumular: sem aprovação, a pessoa não entra no sistema.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> Administrador e gestor central não dependem desse vínculo para circular na rede, mas o profissional da ponta sim. Sem unidade ativa, o menu de gestão não funciona.</p>
'''
            },
        ],
    },
    {
        'name': 'Relatórios, contratos e configurações',
        'description': 'Exportar dados, olhar contratos e ajustar o que a unidade vê nos selects.',
        'pages': [
            {
                'name': 'Relatórios e exportação',
                'html': '''
<p>Menu <strong>Gestão da Unidade → Relatórios</strong>. A tela inicial é um conjunto de cartões. Cada relatório traz filtro (unidade, período, status, conforme o tema) e exportação em Excel ou CSV.</p>
<p>Exemplos: inventário, salas, profissionais, contratos, empenhos, aniversariantes, faltas abonadas, <strong>segurança do paciente</strong>, mapa da saúde.</p>
<p class="callout info"><strong>Permissão:</strong> quem não vê todas as unidades só exporta o que pode ver. Isso é regra de segurança, não filtro “quebrado”.</p>
'''
            },
            {
                'name': 'Contratos, empenho e empresas',
                'html': '''
<p>Essas telas ficam em <strong>Gestão Financeira</strong> e só aparecem para quem tem permissão.</p>
<ul>
<li><strong>Contratos</strong> — vigência, identificador, mandado judicial quando houver. Há resumo para impressão.</li>
<li><strong>Controle de empenho</strong> — fontes e empenhos ligados ao contrato.</li>
<li><strong>Empresas</strong> — cadastro de contratadas.</li>
<li><strong>Emendas</strong> e <strong>Licitações</strong> — acompanhamento da linha SUEQ, quando o módulo estiver em uso na rede.</li>
</ul>
<p class="callout success"><strong>Dica:</strong> O detalhe do contrato também usa o modal de impressão institucional do SIGUS.</p>
'''
            },
            {
                'name': 'Configurações, perfis e auditoria',
                'html': '''
<p>Área sensível. Em geral é da Saúde Digital / administração do sistema, com apoio da coordenação.</p>
<h2>Gestão de perfis</h2>
<p>Em <strong>Configurações → Gestão de Perfis</strong> cada perfil ganha Ver / Editar / Adicionar por seção. Mudar aqui altera o menu de todo mundo daquele perfil.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> Não “teste” permissão em produção no perfil de toda a rede. Ajuste com cuidado e comunique a coordenação.</p>
<h2>Listas da Segurança do Paciente</h2>
<p>Os selects da notificação (status, classificação, tipo de incidente, setor, destino…) não estão fixos no código. Inclua, desative ou marque “pede texto Outro” e “jamais deveria ocorrer” em <strong>Configurações → Segurança do Paciente</strong>. Item desativado some dos formulários novos e permanece no histórico antigo.</p>
<h2>Feriados, usuários, links úteis</h2>
<p>Feriados alimentam a agenda. Usuários: alta, inativação, vínculo. Links úteis: atalhos que a equipe vê no menu da unidade.</p>
<h2>Auditoria</h2>
<p>Quase toda ação relevante (login, alteração, exclusão) pode ser consultada em <strong>Configurações → Auditoria</strong>, por quem tiver permissão. Por isso o login precisa ser individual.</p>
'''
            },
        ],
    },
]


def publish(s: requests.Session) -> None:
    api(s, 'PUT', f'/books/{BOOK_ID}', json={
        'name': 'Manuais de utilização do SIGUS',
        'description_html': BOOK_DESC,
    })
    print('Livro atualizado (descrição).')

    existing = api(s, 'GET', f'/books/{BOOK_ID}')
    already = {c['name']: c for c in existing.get('contents', []) if c.get('type') == 'chapter'}

    for i, ch in enumerate(CHAPTERS, start=1):
        if ch['name'] in already:
            chapter = already[ch['name']]
            cid = chapter['id']
            print(f'Capítulo já existia: {ch["name"]} (id={cid})')
            pages_exist = {p['name']: p for p in chapter.get('pages', [])}
        else:
            chapter = api(s, 'POST', '/chapters', json={
                'book_id': BOOK_ID,
                'name': ch['name'],
                'description': ch['description'],
                'priority': i,
            })
            cid = chapter['id']
            pages_exist = {}
            print(f'Capítulo criado: {ch["name"]} (id={cid})')

        for j, pg in enumerate(ch['pages'], start=1):
            if pg['name'] in pages_exist:
                pid = pages_exist[pg['name']]['id']
                api(s, 'PUT', f'/pages/{pid}', json={'name': pg['name'], 'html': pg['html']})
                print(f'  página atualizada: {pg["name"]}')
            else:
                created = api(s, 'POST', '/pages', json={
                    'chapter_id': cid,
                    'name': pg['name'],
                    'html': pg['html'],
                    'priority': j,
                })
                print(f'  página criada: {pg["name"]} -> {created.get("url") or created.get("slug")}')


def main():
    s = session_login()
    publish(s)
    print('OK. Abra', f'{BASE}/books/manuais-de-utilizacao-do-sigus')


if __name__ == '__main__':
    main()
