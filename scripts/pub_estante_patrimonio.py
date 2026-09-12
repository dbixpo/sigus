# -*- coding: utf-8 -*-
"""Publica o capítulo especial de patrimônio (salas, equipamentos, transferências e lojinha)
no livro Manuais de utilização do SIGUS (Estante SES / BookStack).

Credenciais só por variável de ambiente. Não versionar senha.
  ESTANTE_EMAIL  ESTANTE_SENHA
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = 'https://estante-ses.sorocaba.sp.gov.br'
BOOK_ID = 45
SIGUS_URL = 'https://saudedigital.sorocaba.sp.gov.br/sigus'
SHOT = Path(__file__).resolve().parents[1] / 'app' / 'static' / 'uploads' / 'manuais_tmp'
CHAPTER_NAME = 'Patrimônio: salas, equipamentos, transferências e lojinha'


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
    r = s.request(method, f'{BASE}/api{path}', timeout=90, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f'{method} {path} -> {r.status_code}: {r.text[:800]}')
    return r.json() if r.content else {}


def fig(url: str, alt: str) -> str:
    return (
        f'<p><a href="{url}" target="_blank" rel="noopener">'
        f'<img src="{url}" alt="{alt}"></a></p>'
    )


def upload_shot(s: requests.Session, page_id: int, stem: str, alt: str) -> str:
    path = SHOT / f'{stem}.png'
    if not path.exists():
        print(f'  aviso: print ausente {path.name}')
        return ''
    with path.open('rb') as f:
        r = s.post(
            f'{BASE}/api/image-gallery',
            data={'type': 'gallery', 'uploaded_to': str(page_id), 'name': f'{stem}.png'},
            files={'image': (f'{stem}.png', f, 'image/png')},
            timeout=90,
        )
    if r.status_code >= 400:
        raise RuntimeError(f'upload {stem}: {r.status_code} {r.text[:400]}')
    data = r.json()
    url = ((data.get('thumbs') or {}).get('display')) or data.get('url')
    return fig(url, alt)


def pages():
    return [
        {
            'name': 'Como o patrimônio funciona no SIGUS',
            'shots': [],
            'html': f'''
<p>Este capítulo é o manual <strong>tela a tela</strong> do patrimônio no SIGUS: as <strong>salas</strong> da unidade, o <strong>cadastro e a gestão dos equipamentos</strong>, os <strong>termos de transferência e empréstimo</strong> e a <strong>Lojinha Interna</strong>.</p>
<p>A regra de ouro: o equipamento <strong>mora numa sala</strong>, e a sala <strong>mora numa unidade</strong>. Chamado, transferência e lojinha usam esse endereço. Sem sala certa, o bem “some” na hora de achar, transferir ou abrir manutenção.</p>
<h2>O caminho que você vai percorrer</h2>
<table>
<thead><tr><th>O que você precisa fazer</th><th>Onde no SIGUS</th></tr></thead>
<tbody>
<tr><td>Cadastrar ou conferir as salas do prédio</td><td>Ficha da unidade → aba <strong>Salas/Setores</strong></td></tr>
<tr><td>Cadastrar um bem permanente</td><td>Ficha da unidade → aba <strong>Equipamentos</strong>, ou a partir da sala</td></tr>
<tr><td>Ver todos os bens da rede (com filtro)</td><td>Lista de <strong>Equipamentos</strong> e relatório de <strong>Inventário</strong></td></tr>
<tr><td>Mandar um bem para outra unidade</td><td>Ficha do equipamento → <strong>Transferir</strong>, ou <strong>Operações → Transferências → Novo Termo</strong></td></tr>
<tr><td>Oferecer o que a unidade não usa mais</td><td>Aba <strong>Lojinha Interna</strong></td></tr>
</tbody>
</table>
{c('info', 'Acesso:', f'Tudo isso está em <a href="{SIGUS_URL}">{SIGUS_URL}</a>. O menu só mostra o que o seu perfil pode ver.')}
{c('warning', 'ATENÇÃO:', 'Não apague um equipamento de uma unidade para “cadastrar de novo” em outra. O histórico patrimonial se perde. Use transferência, aceite e — quando for o caso — a Lojinha.')}
{c('success', 'Dica:', 'Comece pelas salas. Só depois cadastre equipamentos. O próprio formulário do bem pede a sala e oferece o atalho “Criar nova sala”.')}
'''
        },
        {
            'name': 'Aba Salas na ficha da unidade',
            'shots': [('un-salas', 'Ficha da unidade com a aba Salas/Setores aberta')],
            'html': f'''
<p>Abra a <strong>ficha da sua unidade</strong> (menu Gestão da Unidade → Unidades, ou o atalho da unidade no menu). No topo você vê os totais: salas ativas, equipamentos, chamados em aberto e profissionais.</p>
<p>Clique na aba <strong>Salas/Setores</strong>. É a lista oficial dos ambientes do prédio: consultório, recepção, farmácia, coordenação, arquivo etc.</p>
<h2>O que a lista mostra</h2>
<ul>
<li><strong>Sala/Setor</strong> — o nome que a equipe usa no dia a dia.</li>
<li><strong>Tipo</strong> — consultório, recepção, administração… vem do cadastro de tipos.</li>
<li><strong>Ramal</strong> — se a sala tem telefone próprio.</li>
<li><strong>Equipamentos</strong> — quantos bens estão alocados ali.</li>
<li>Botões <strong>Ver</strong> e lápis (editar).</li>
</ul>
<h2>Como chegar</h2>
<ol>
<li>Abra a ficha da unidade.</li>
<li>Clique em <strong>Salas/Setores</strong>.</li>
<li>Use a busca “Buscar em qualquer coluna…” para achar pelo nome, tipo ou ramal.</li>
<li>Para incluir: botão azul <strong>Nova Sala/Setor</strong> no canto superior direito, ou o <strong>+</strong> no cabeçalho da lista.</li>
</ol>
{{SHOT0}}
{c('info', 'Campos com *:', 'Nome, tipo e máximo de profissionais simultâneos são obrigatórios no cadastro da sala.')}
{c('success', 'Dica:', 'Mantenha o nome igual ao que está na porta. “Sala 01” e “Consultório 1” para o mesmo cômodo geram equipamento no lugar errado.')}
'''
        },
        {
            'name': 'Cadastrar nova sala',
            'shots': [('sala-nova', 'Formulário Nova Sala')],
            'html': f'''
<p>Na ficha da unidade, clique em <strong>Nova Sala/Setor</strong>. O formulário já nasce ligado àquela unidade — você não escolhe a unidade de novo.</p>
<h2>Preencha nesta ordem</h2>
<ol>
<li><strong>Nome da Sala *</strong> — o nome da porta (ex.: Consultório 1, Sala de Enfermagem A).</li>
<li><strong>Tipo de Sala *</strong> — escolha na lista. Se o tipo não existir, use o link <em>Cadastrar novo tipo de sala</em> (abre Configurações; precisa de permissão).</li>
<li><strong>Responsável</strong> — opcional. Nome de quem “cuida” da sala.</li>
<li><strong>Máx. profissionais simultâneos *</strong> — quantas pessoas usam a sala <strong>ao mesmo tempo</strong>, não no turno inteiro. O ícone de informação explica com exemplos: consultório em geral 1; consultório de GO em geral 2; recepção/coordenação = todo mundo que trabalha junto.</li>
<li><strong>Ramal</strong> — opcional.</li>
<li><strong>Observações</strong> — o que a equipe precisa lembrar (ex.: “pós-consulta das especialidades”).</li>
<li>Clique em <strong>Cadastrar Sala</strong>.</li>
</ol>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Não informe o máximo “por período” (manhã/tarde). Informe o maior número possível no mesmo momento.')}
{c('success', 'Dica:', 'Depois de salvar, a sala aparece na aba Salas e já pode receber equipamentos.')}
'''
        },
        {
            'name': 'Ver a sala: equipamentos e chamados',
            'shots': [
                ('sala-detalhe', 'Detalhe da sala com a aba Equipamentos'),
                ('sala-chamados', 'Aba Chamados da mesma sala'),
            ],
            'html': f'''
<p>Na lista de salas, clique em <strong>Ver</strong> (ou no nome). Você entra na <strong>ficha da sala</strong>: nome, tipo, ramal, datas de criação e atualização.</p>
<h2>Aba Equipamentos</h2>
<p>É a lista dos bens alocados nesta sala: patrimônio, tipo, marca/modelo, status, condição e série. Clique na linha ou em <strong>Ver</strong> para abrir o equipamento.</p>
<p>Se você pode cadastrar patrimônio, o botão <strong>Novo Equipamento</strong> já nasce nesta sala — você não precisa escolher a sala de novo.</p>
{{SHOT0}}
<h2>Aba Chamados</h2>
<p>Mostra os chamados ligados à sala ou aos equipamentos dela. Use para ver se aquele consultório está com manutenção aberta antes de transferir ou realocar o bem.</p>
{{SHOT1}}
{c('info', 'Novo Equipamento:', 'O botão só aparece para quem tem a permissão de cadastrar equipamento.')}
'''
        },
        {
            'name': 'Editar sala',
            'shots': [('sala-editar', 'Formulário Editar Sala')],
            'html': f'''
<p>Na lista ou na ficha da sala, clique no lápis. É o mesmo formulário da criação, já preenchido.</p>
<p>Altere nome, tipo, responsável, máximo de profissionais, ramal ou observações e clique em <strong>Salvar Alterações</strong>.</p>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Mudar o nome da sala não move os equipamentos: eles continuam nesta sala, só com o rótulo novo. Para mudar o bem de cômodo, edite o <strong>equipamento</strong> e escolha outra sala da mesma unidade.')}
{c('info', 'Desativar:', 'Quem tem permissão pode desativar sala que não existe mais no prédio. Prefira desativar a apagar: o histórico dos equipamentos permanece.')}
'''
        },
        {
            'name': 'Cadastro externo de salas (sem login)',
            'shots': [('sala-externo', 'Tela pública de cadastro de salas por unidade')],
            'html': f'''
<p>Existe uma tela <strong>fora do menu logado</strong> para cadastrar salas em lote, unidade por unidade: <strong>Cadastro Externo de Salas</strong>. Serve para mutirão de inventário (apoio no próprio serviço, sem precisar de perfil completo no SIGUS).</p>
<h2>Como usar</h2>
<ol>
<li>Abra o endereço do cadastro externo (a coordenação ou a Saúde Digital envia o link).</li>
<li>Em <strong>Unidade de Saúde</strong>, busque e selecione a unidade. A lista é grande: digite parte do nome.</li>
<li>Preencha nome *, tipo, responsável, máximo de profissionais *, ramal e observações — iguais ao cadastro interno.</li>
<li>Clique em <strong>Salvar e Adicionar outro</strong>. A sala entra na lista de baixo e o formulário fica pronto para a próxima.</li>
<li>Para corrigir uma sala já listada, use o lápis da linha.</li>
</ol>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Essa tela cadastra ambiente do prédio. Não use para equipamento, chamado ou transferência. Depois do mutirão, a equipe logada confere a aba Salas na ficha da unidade.')}
{c('success', 'Dica:', 'Escolha a unidade certa antes de sair salvando. Sala gravada na unidade errada precisa ser corrigida depois, uma a uma.')}
'''
        },
        {
            'name': 'Tipos de sala',
            'shots': [
                ('cfg-tipos-sala', 'Lista de tipos de sala em Configurações'),
                ('cfg-tipo-sala-novo', 'Formulário de novo tipo de sala'),
            ],
            'html': f'''
<p>O select “Tipo de Sala” não é texto livre: vem de <strong>Configurações → Tipos de Sala</strong>. Só quem tem permissão de configurações altera essa lista.</p>
<h2>Lista de tipos</h2>
<p>Cada linha tem ícone, nome, descrição, quantas salas ativas usam aquele tipo, status (ativo/inativo) e ações de editar ou ligar/desligar.</p>
{{SHOT0}}
<h2>Novo tipo</h2>
<ol>
<li>Clique em <strong>Novo Tipo</strong>.</li>
<li>Informe o <strong>Nome *</strong> (Consultório, Sala de Enfermagem, Recepção…).</li>
<li>Escolha o <strong>ícone</strong> Font Awesome, se quiser.</li>
<li>Descrição é opcional. Salve.</li>
</ol>
{{SHOT1}}
{c('info', 'Tipo inativo:', 'Some dos formulários novos, mas as salas antigas continuam com o tipo que já tinham.')}
{c('warning', 'ATENÇÃO:', 'Não crie tipo duplicado com nome parecido (“Consultorio” e “Consultório”). A busca na unidade fica confusa.')}
'''
        },
        {
            'name': 'Aba Equipamentos na ficha da unidade',
            'shots': [('un-equips', 'Ficha da unidade com a aba Equipamentos')],
            'html': f'''
<p>Na mesma ficha da unidade, abra a aba <strong>Equipamentos</strong>. É o inventário daquele serviço: tipo, patrimônio ou série, marca/modelo, usuário vinculado, sala, status e condição.</p>
<h2>O que você faz aqui</h2>
<ul>
<li>Buscar em qualquer coluna ou filtrar por sala.</li>
<li><strong>Exportar CSV</strong> da lista da unidade.</li>
<li><strong>Novo Equipamento</strong> — abre o cadastro já no contexto desta unidade (você escolhe a sala).</li>
<li>O ícone de olho abre a ficha do bem.</li>
</ul>
{{SHOT0}}
{c('warning', 'IMPORTANTE:', 'Para cadastrar equipamento a unidade precisa ter <strong>pelo menos uma sala ativa</strong>. Sem sala, o botão não resolve: volte na aba Salas e crie o ambiente primeiro.')}
{c('success', 'Dica:', 'Use o filtro de sala quando for conferir só um consultório ou só a coordenação.')}
'''
        },
        {
            'name': 'Lista geral de equipamentos',
            'shots': [('eq-lista', 'Tela Equipamentos com filtros e listagem da rede')],
            'html': f'''
<p>Além da aba da unidade, existe a lista geral de <strong>Equipamentos</strong> (quem tem permissão de ver o inventário da rede ou das suas unidades). Use quando o bem “não está na unidade que eu pensei”.</p>
<h2>Filtros</h2>
<ul>
<li>Tipo de unidade, unidade, tipo de equipamento, status e condição.</li>
<li>A lupa aplica; o X limpa e volta à lista completa do seu alcance.</li>
</ul>
<p>A tabela mostra identificação (patrimônio), marca/modelo, unidade/sala, usuários, status, condição, contrato e o botão <strong>Ver</strong>.</p>
{{SHOT0}}
{c('info', 'Permissão:', 'Quem não vê todas as unidades só lista o que o perfil alcança. Isso é regra de segurança, não filtro quebrado.')}
'''
        },
        {
            'name': 'Cadastrar equipamento',
            'shots': [
                ('eq-novo', 'Novo equipamento a partir da unidade (escolhe a sala)'),
                ('eq-novo-sala', 'Novo equipamento já preso a uma sala'),
            ],
            'html': f'''
<p>Há dois jeitos de chegar no mesmo formulário:</p>
<ul>
<li>Na aba Equipamentos da unidade → <strong>Novo Equipamento</strong>. Você <strong>escolhe a sala</strong> (ou cria uma nova em outra aba).</li>
<li>Na ficha da sala → <strong>Novo Equipamento</strong>. A sala já vem preenchida.</li>
</ul>
{{SHOT0}}
<h2>Identificação</h2>
<ol>
<li><strong>Sala *</strong> — onde o bem está hoje.</li>
<li><strong>Tipo de Equipamento *</strong> — computador, monitor, ar-condicionado… Depois do tipo, o sistema libera marca, modelo e os campos extras daquele tipo (RAM, processador, BTUs…).</li>
<li><strong>Nº de Patrimônio</strong> — digite só os números; o prefixo <strong>PMS-</strong> entra sozinho.</li>
<li><strong>Nº de Série</strong> — útil quando ainda não há patrimônio.</li>
<li><strong>Marca</strong> e <strong>Modelo</strong> — encadeados: primeiro o tipo, depois a marca, depois o modelo. Se faltar marca, há atalho para Configurações.</li>
</ol>
<h2>Estado, condição e extras</h2>
<ul>
<li><strong>Status *</strong> (em geral Ativo) e <strong>Condição *</strong> (Boa, Regular, Ruim…).</li>
<li>Ano de aquisição, valor estimado, tempo de uso e observações.</li>
<li>Opcional: vincular já o usuário que usa o equipamento.</li>
</ul>
{{SHOT1}}
{c('info', 'Tipo primeiro:', 'Marca e modelo ficam bloqueados até você escolher o tipo. É de propósito, para não misturar “HP de computador” com “HP de impressora”.')}
{c('warning', 'ATENÇÃO:', 'Confira o número de patrimônio na plaqueta. Patrimônio duplicado ou invertido atrapalha transferência e chamado de bem permanente.')}
'''
        },
        {
            'name': 'Ficha do equipamento: gestão do bem',
            'shots': [
                ('eq-detalhe', 'Ficha do equipamento com dados, status e ações'),
                ('eq-usuarios', 'Aba Usuários: vincular quem usa o equipamento'),
            ],
            'html': f'''
<p>A ficha do equipamento é o “RG” do bem. No topo: nome (tipo + marca + modelo), patrimônio e os botões de ação — conforme a sua permissão.</p>
<h2>Botões do topo</h2>
<table>
<thead><tr><th>Botão</th><th>Quando usar</th></tr></thead>
<tbody>
<tr><td>Editar</td><td>Corrigir dados ou realocar para outra sala da <strong>mesma</strong> unidade.</td></tr>
<tr><td>Abrir Chamado</td><td>Manutenção de <strong>bem permanente</strong> já amarrada neste patrimônio.</td></tr>
<tr><td>Transferir</td><td>Mandar o bem para outra unidade (a destino ainda precisa aceitar).</td></tr>
<tr><td>Dar Baixa</td><td>O bem saiu de uso (sucata, extravio formalizado etc.). Não substitui transferência.</td></tr>
</tbody>
</table>
<p>À direita: status (Ativo), condição, contrato vinculado (se houver), quem usa, datas de criação e atualização. A localização é um caminho clicável: <strong>unidade › sala</strong>.</p>
{{SHOT0}}
<h2>Abas de baixo</h2>
<ul>
<li><strong>Chamados</strong> — histórico de manutenção deste bem.</li>
<li><strong>Ciclo de vida</strong> — eventos (cadastro, transferência, baixa).</li>
<li><strong>Transferências</strong> — termos em que este bem entrou.</li>
<li><strong>Usuários</strong> — vincule o profissional que usa o computador, o ramal, o aparelho. Informe uma observação se quiser (ex.: “responsável principal”).</li>
</ul>
{{SHOT1}}
{c('warning', 'Dar baixa:', 'Confirme com calma. Baixa tira o bem da operação. Se ele só mudou de unidade, use Transferir.')}
{c('success', 'Dica:', 'Chamado de bem permanente pela ficha do equipamento já nasce com o patrimônio certo. Evite chamado “solto”.')}
'''
        },
        {
            'name': 'Editar equipamento',
            'shots': [('eq-editar', 'Formulário Editar Equipamento')],
            'html': f'''
<p>Na ficha, clique em <strong>Editar</strong>. Você pode:</p>
<ul>
<li>Trocar a <strong>sala</strong> — só entre salas da <strong>mesma unidade</strong> (realocação interna). Mudança de unidade é transferência.</li>
<li>Corrigir patrimônio, série, marca, modelo, condição, status, ano, valor, observações e campos do tipo (SSD, RAM, processador…).</li>
</ul>
<p>Se o sistema permitir alterar o tipo, um aviso amarelo aparece: <strong>mudar o tipo apaga os campos específicos do tipo anterior</strong>.</p>
{{SHOT0}}
{c('info', 'PMS-:', 'Na edição, o prefixo continua automático. Digite só a parte numérica.')}
{c('warning', 'ATENÇÃO:', 'Realocar de sala não gera termo de transferência. Só muda o endereço dentro da unidade.')}
'''
        },
        {
            'name': 'Tipos de equipamento, marcas e modelos',
            'shots': [
                ('cfg-tipos-eq', 'Lista de tipos de equipamento'),
                ('cfg-tipo-eq-editar', 'Edição de tipo com campos personalizados'),
                ('cfg-marcas', 'Árvore Tipo → Marcas → Modelos'),
            ],
            'html': f'''
<p>Quem cadastra o bem na ponta escolhe tipo, marca e modelo. Quem administra o sistema monta essas listas em <strong>Configurações</strong>.</p>
<h2>Tipos de equipamento</h2>
<p>Em <strong>Configurações → Tipos de Equipamento</strong> você vê ícone, nome, se exige patrimônio, quantos campos extras existem, quantos bens usam o tipo e se está ativo.</p>
{{SHOT0}}
<h2>Campos extras do tipo</h2>
<p>Ao editar um tipo (ex.: Computador All-in-One), o lado direito lista campos como SSD, capacidade de disco, processador, RAM, sistema operacional. Cada campo tem tipo de dado (texto, número, sim/não, seleção) e pode ser obrigatório.</p>
<p>Esses campos aparecem no cadastro do equipamento depois que você escolhe o tipo.</p>
{{SHOT1}}
<h2>Marcas e modelos</h2>
<p>Em <strong>Configurações → Marcas e Modelos</strong> a árvore é <strong>Tipo → Marcas daquele tipo → Modelos</strong>. Cadastre marca e modelo no tipo certo, senão o select do formulário fica vazio.</p>
{{SHOT2}}
{c('success', 'Dica:', 'Marque “Possui Nº de Patrimônio” nos tipos que são bem permanente. Itens de consumo não precisam de plaqueta PMS.')}
'''
        },
        {
            'name': 'Relatórios de inventário e de salas',
            'shots': [
                ('rel-hub', 'Hub de Relatórios e Inventários'),
                ('rel-inventario', 'Inventário de Equipamentos'),
                ('rel-salas', 'Relatório de Salas'),
            ],
            'html': f'''
<p>Para conferência, auditoria ou planilha, não copie a tela: use <strong>Gestão da Unidade → Relatórios</strong>.</p>
{{SHOT0}}
<h2>Inventário de Equipamentos</h2>
<p>Filtros por tipo de unidade, unidade, status, condição, patrimônio, tipo, marca, modelo, série, sala e contrato. Dá para imprimir e exportar.</p>
{{SHOT1}}
<h2>Relatório de Salas</h2>
<p>Quantos consultórios, recepções e outros tipos existem, com filtro de chamado em aberto. Também exporta Excel/CSV e imprime.</p>
{{SHOT2}}
{c('info', 'Permissão:', 'Quem não vê todas as unidades só exporta o recorte que pode ver.')}
'''
        },
        {
            'name': 'Transferências — pendentes de aceite',
            'shots': [('tr-pendentes', 'Aba Pendentes de aceite')],
            'html': f'''
<p>Abra <strong>Operações → Transferências</strong>. Quatro abas: <strong>Pendentes de aceite</strong>, <strong>Enviadas</strong>, <strong>Concluídas</strong> e <strong>Lojinha Interna</strong>.</p>
<p>A aba <strong>Pendentes de aceite</strong> é a caixa de entrada da <strong>unidade de destino</strong>: termos que alguém mandou para você e ainda não foram aceitos nem recusados.</p>
<p>Colunas: tipo (transferência, empréstimo, doação), de, para, quem criou, quantos itens, data. Ações: cancelar (quando couber) e imprimir o termo no modal padrão do SIGUS.</p>
<p>O botão azul <strong>Novo Termo</strong> abre o cadastro de um documento novo.</p>
{{SHOT0}}
{c('warning', 'Unidade no topo:', 'Para aceitar em nome de uma unidade, selecione essa unidade no seletor do cabeçalho. Sem unidade de trabalho, o sistema não sabe em nome de quem você está aceitando.')}
{c('info', 'Impresso:', 'Use a impressora do SIGUS para o termo físico e as assinaturas. O documento digital continua no sistema.')}
'''
        },
        {
            'name': 'Transferências — enviadas',
            'shots': [('tr-enviadas', 'Aba Enviadas aguardando aceite')],
            'html': f'''
<p>A aba <strong>Enviadas</strong> mostra o que a sua origem já despachou e ainda espera o aceite do destino. Serve para cobrar: “o termo saiu daqui; está na caixa de pendentes da outra unidade”.</p>
{{SHOT0}}
{c('success', 'Dica:', 'Se o destino não aceita, ligue e confira patrimônio e sala. Cancelar e refazer com o item errado é pior do que um telefonema.')}
'''
        },
        {
            'name': 'Transferências — concluídas',
            'shots': [('tr-concluidas', 'Aba Concluídas com status aceita ou cancelada')],
            'html': f'''
<p>A aba <strong>Concluídas</strong> é o histórico: aceita, recusada ou cancelada. Há filtro de status. A impressora continua disponível para o termo.</p>
<p>Aqui também aparecem <strong>doações</strong> geradas pela Lojinha, depois de resolvidas.</p>
{{SHOT0}}
{c('info', 'Não some o histórico:', 'Concluída não é exclusão. O bem que foi aceito já está na sala do destino; o termo fica para auditoria.')}
'''
        },
        {
            'name': 'Novo termo de transferência ou empréstimo',
            'shots': [('termo-novo', 'Formulário Novo Termo')],
            'html': f'''
<p>Em Transferências, clique em <strong>Novo Termo</strong>. Use quando for um lote (vários itens) ou quando o bem ainda não está “no botão Transferir” da ficha.</p>
<h2>Cabeçalho</h2>
<ol>
<li>Marque <strong>Empréstimo</strong> ou <strong>Transferência</strong> (obrigatório).</li>
<li>Escolha <strong>unidade de origem *</strong> e <strong>unidade de destino *</strong>.</li>
<li>Observação é opcional (motivo, estado do bem, instrução de retirada).</li>
</ol>
<h2>Materiais</h2>
<ul>
<li><strong>Do inventário</strong> — busca o bem já cadastrado (patrimônio, tipo, sala).</li>
<li><strong>Item manual</strong> — descreve o que ainda não está no cadastro (o aceite pode criar no inventário do destino).</li>
</ul>
<p>Cada linha tem quantidade, descrição, patrimônio/série e <strong>classificação</strong>:</p>
<ul>
<li><strong>A</strong> — inservível ao setor, porém com plenas condições de uso.</li>
<li><strong>B</strong> — inservível ao setor, usa, mas precisa de reparo.</li>
</ul>
<p>Clique em <strong>Criar documento</strong>. O termo aparece em Enviadas na origem e em Pendentes no destino.</p>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Empréstimo e transferência não são a mesma coisa. Empréstimo pressupõe volta; transferência muda o dono operacional do bem na rede.')}
'''
        },
        {
            'name': 'Solicitar transferência a partir do equipamento',
            'shots': [('tr-solicitar', 'Tela Solicitar Transferência com o bem já identificado')],
            'html': f'''
<p>Na ficha de um equipamento <strong>ativo</strong>, clique em <strong>Transferir</strong>. O lado esquerdo já traz tipo, patrimônio, marca, modelo, sala e unidade atuais. Você só informa o destino.</p>
<ol>
<li>Escolha a <strong>unidade de destino *</strong>.</li>
<li>Observação opcional: motivo, estado, como vai ser o transporte.</li>
<li>Clique em <strong>Solicitar Transferência</strong>.</li>
</ol>
<p>O fluxo na tela: você solicita → o coordenador da unidade destino recebe → ele aceita e aloca em uma sala, ou recusa.</p>
{{SHOT0}}
{c('info', 'Permissão:', 'O botão Transferir só aparece se você pode solicitar transferência e o bem não está baixado.')}
'''
        },
        {
            'name': 'Aceitar ou recusar o documento',
            'shots': [('tr-aceitar', 'Tela Resolver Termo: aceitar alocando em uma sala ou recusar')],
            'html': f'''
<p>Na aba Pendentes, abra o termo. A tela <strong>Resolver Termo</strong> mostra os materiais, origem, destino, quem criou e a data.</p>
<h2>Aceitar</h2>
<ol>
<li>Confira se o patrimônio da lista é o que chegou na portaria.</li>
<li>Em <strong>Alocar em qual sala? *</strong>, escolha a sala da <strong>sua</strong> unidade. O bem vai para essa sala na hora.</li>
<li>Observação de aceite é opcional.</li>
<li>Clique em <strong>Aceitar e Alocar</strong>.</li>
</ol>
<p>Se o item tinha patrimônio/série e ainda não existia no inventário, o SIGUS pode cadastrá-lo na sala escolhida. Se não conseguir localizar nem cadastrar, o aceite não conclui — o sistema lista o que faltou.</p>
<h2>Recusar</h2>
<p>Informe o motivo e clique em <strong>Recusar</strong>. O bem permanece na origem.</p>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Aceite sem conferir a plaqueta coloca patrimônio errado na sua unidade. Recusar com motivo claro é melhor do que aceitar “para depois ver”.')}
{c('info', 'Seu seletor de unidade:', 'O aceite é em nome da unidade de trabalho do topo. Se o termo é para o SAMU, trabalhe como SAMU; se é para a UBS, selecione a UBS.')}
'''
        },
        {
            'name': 'Lojinha Interna — vitrine e carrinho',
            'shots': [('tr-lojinha', 'Aba Lojinha Interna com itens agrupados por unidade')],
            'html': f'''
<p>A <strong>Lojinha Interna</strong> é a vitrine do que as unidades colocaram à disposição: equipamento que o setor não usa mais, mas outra unidade da rede ainda pode aproveitar. Não é loja para o cidadão. É circulação interna de patrimônio.</p>
<p>Caminho: <strong>Operações → Transferências → aba Lojinha Interna</strong>. O botão verde <strong>Cadastrar Equipamento para Doação</strong> abre a tela de colocar item à disposição.</p>
<h2>O que você vê</h2>
<ul>
<li>Itens agrupados pela <strong>unidade que está doando</strong>, com telefone e e-mail do serviço para combinar a retirada.</li>
<li>Quantidade, descrição, patrimônio/série, classificação A ou B, quem disponibilizou e quando.</li>
<li>Busca por descrição e filtro de classificação.</li>
</ul>
<h2>Pegar um item (outra unidade)</h2>
<ol>
<li>Selecione a <strong>sua</strong> unidade no topo — a compra nasce para essa unidade.</li>
<li>No item de <strong>outra</strong> unidade, clique no carrinho.</li>
<li>Confirme a quantidade.</li>
<li>Abra o carrinho e <strong>finalize</strong>. O SIGUS gera documento(s) de doação/transferência em Pendentes para você aceitar e alocar em uma sala.</li>
</ol>
<h2>Item da sua própria unidade</h2>
<p>Em vez do carrinho, aparece a lixeira: você <strong>retira da vitrine</strong> (o bem deixou de estar à disposição). Não dá para “comprar de si mesmo”.</p>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Não dá para finalizar o carrinho sem unidade selecionada no topo. Também não entram itens da sua própria unidade.')}
{c('success', 'Dica:', 'Classificação A = pronto para usar. B = precisa de reparo. Leia a descrição (ex.: “precisa de cabo”) antes de colocar no carrinho.')}
{c('info', 'Depois de finalizar:', 'O documento aparece em Pendentes. Ainda falta o aceite com a sala de destino — igual a qualquer termo.')}
'''
        },
        {
            'name': 'Lojinha — colocar item à disposição',
            'shots': [('lojinha-add', 'Tela Colocar à disposição')],
            'html': f'''
<p>Na Lojinha, clique em <strong>Cadastrar Equipamento para Doação</strong>. Esta tela publica o que a sua unidade não precisa mais.</p>
<ol>
<li>Escolha a <strong>Unidade *</strong> que está disponibilizando.</li>
<li>Inclua itens <strong>do inventário</strong> (bem já cadastrado) ou <strong>item manual</strong> (descrição livre).</li>
<li>Informe quantidade, patrimônio/série se houver, e classificação <strong>A</strong> ou <strong>B</strong>.</li>
<li>Clique em <strong>Adicionar à Lojinha</strong>.</li>
</ol>
<p>O item entra na vitrine para as outras unidades. Quem for da mesma unidade vê a opção de retirar; as demais veem o carrinho.</p>
{{SHOT0}}
{c('warning', 'ATENÇÃO:', 'Colocar na Lojinha não transfere sozinho. Só publica. A transferência de verdade acontece quando outra unidade finaliza o carrinho e a origem/destino concluem o termo (aceite + sala).')}
{c('info', 'Classificação:', 'A — inservível ao setor, plenas condições de uso. B — inservível ao setor, usa mas precisa de reparo.')}
'''
        },
    ]


def ensure_chapter(s: requests.Session) -> tuple[int, dict]:
    book = api(s, 'GET', f'/books/{BOOK_ID}')
    already = {c['name']: c for c in book.get('contents', []) if c.get('type') == 'chapter'}
    if CHAPTER_NAME in already:
        ch = already[CHAPTER_NAME]
        print(f'Capítulo já existia id={ch["id"]}')
        return ch['id'], {p['name']: p for p in ch.get('pages', [])}
    created = api(s, 'POST', '/chapters', json={
        'book_id': BOOK_ID,
        'name': CHAPTER_NAME,
        'description': (
            'Cadastro de salas e equipamentos, gestão do bem, termos de '
            'transferência/empréstimo e a Lojinha Interna — uma página para cada tela.'
        ),
        'priority': 3,
    })
    print(f'Capítulo criado id={created["id"]}')
    return created['id'], {}


def upsert_page(s, cid: int, exist: dict, name: str, html: str, priority: int) -> int:
    if name in exist:
        pid = exist[name]['id']
        api(s, 'PUT', f'/pages/{pid}', json={'name': name, 'html': html})
        print(f'  atualizada: {name} ({pid})')
        return pid
    created = api(s, 'POST', '/pages', json={
        'chapter_id': cid,
        'name': name,
        'html': html,
        'priority': priority,
    })
    pid = created['id']
    print(f'  criada: {name} -> {created.get("url") or pid}')
    return pid


def publish(s: requests.Session) -> None:
    cid, exist = ensure_chapter(s)
    for i, pg in enumerate(pages(), start=1):
        html = pg['html']
        pid = upsert_page(s, cid, exist, pg['name'], html.replace('{SHOT0}', '').replace('{SHOT1}', '').replace('{SHOT2}', ''), i)
        exist[pg['name']] = {'id': pid, 'name': pg['name']}
        for idx, (stem, alt) in enumerate(pg['shots']):
            print(f'    print {stem}...')
            html = html.replace(f'{{SHOT{idx}}}', upload_shot(s, pid, stem, alt))
        api(s, 'PUT', f'/pages/{pid}', json={'name': pg['name'], 'html': html})
        print(f'    html+prints ok')

    # Aponta a página curta antiga para este capítulo
    book = api(s, 'GET', f'/books/{BOOK_ID}')
    for ch in book.get('contents', []):
        if ch.get('type') != 'chapter':
            continue
        for p in ch.get('pages', []):
            if p.get('name') == 'Transferência de equipamentos' and ch.get('name') != CHAPTER_NAME:
                html = f'''
<p>Quando um bem permanente precisa mudar de unidade, <strong>não apague</strong> o cadastro para criar de novo no destino. Use termo de transferência, empréstimo ou a Lojinha Interna.</p>
<p>O passo a passo <strong>tela a tela</strong> (pendentes, enviadas, novo termo, aceite, lojinha) está no capítulo <strong>{CHAPTER_NAME}</strong> deste mesmo livro.</p>
{c('info', 'Atalho:', 'Abra o sumário do livro e entre em “Patrimônio: salas, equipamentos, transferências e lojinha”.')}
'''
                api(s, 'PUT', f'/pages/{p["id"]}', json={'name': p['name'], 'html': html})
                print('Página curta de Operações atualizada com ponteiro.')
                break


def main():
    missing = [p for pg in pages() for p, _ in pg['shots'] if not (SHOT / f'{p}.png').exists()]
    if missing:
        print('Prints faltando:', ', '.join(missing))
        sys.exit(1)
    s = session_login()
    publish(s)
    print('OK.', f'{BASE}/books/manuais-de-utilizacao-do-sigus')


if __name__ == '__main__':
    main()
