# -*- coding: utf-8 -*-
"""Publica o manual de utilização do SIGUS na Estante SES (BookStack).

Credenciais só por variável de ambiente. Não versionar senha.
  ESTANTE_EMAIL  ESTANTE_SENHA
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

BASE = 'https://estante-ses.sorocaba.sp.gov.br'
BOOK_ID = 45
SIGUS_URL = 'https://saudedigital.sorocaba.sp.gov.br/sigus'
SHOT = Path(__file__).resolve().parents[1] / 'app' / 'static' / 'uploads' / 'manuais_tmp'


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
    if not url:
        raise RuntimeError(f'upload {stem}: resposta sem URL ({data!r})')
    return fig(url, alt)


def strip_shot_placeholders(html: str) -> str:
    for i in range(16):
        html = html.replace(f'{{SHOT{i}}}', '')
    return html


BOOK_DESC = (
    '<p>Aqui você encontra os manuais operacionais do <strong>SIGUS</strong> — '
    'Sistema Integrado de Gestão das Unidades de Saúde da Secretaria da Saúde de Sorocaba.</p>'
    '<p>O SIGUS é a ferramenta da Saúde Digital para a gestão da unidade: patrimônio, '
    'chamados, planejamentos, agenda, segurança do paciente, pessoas, contratos, '
    'comunicados com ciência e o mural de ações da rede. '
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
                'shots': [('dash', 'Dashboard do SIGUS depois do login, com os cartões da rede')],
                'html': f'''
<p>O <strong>SIGUS</strong> (Sistema Integrado de Gestão das Unidades de Saúde) é o sistema da Saúde Digital para organizar o dia a dia das unidades da rede municipal de Sorocaba: o prédio, as salas, os equipamentos, os chamados de manutenção, os planejamentos, a agenda, as pessoas e a segurança do paciente.</p>
<p>Pense nele como a “gestão da casa”. O atendimento clínico do cidadão continua no <strong>SISWEB</strong>. O SIGUS cuida do que faz a unidade funcionar.</p>
{{SHOT0}}
<h2>O que você encontra no sistema</h2>
<table>
<thead><tr><th>Área do menu</th><th>Para que serve</th></tr></thead>
<tbody>
<tr><td>Dashboard</td><td>Dia a dia da unidade: comunicados com ciência, mural de ações, aniversariantes, quem abona hoje e chamados abertos.</td></tr>
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
                'shots': [('login', 'Tela de login do SIGUS com e-mail, senha, Lembrar-me e Entrar')],
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
{{SHOT0}}
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
                'shots': [
                    ('dash-unidade', 'Seletor de unidade de trabalho no topo, aberto sobre o dashboard'),
                    ('usr-perfil-sis', 'Cartão Cadastro no SIS no final da tela Meu Perfil, com o botão de verificar'),
                    ('usr-perfil-sis-resultado', 'Exemplo de consulta concluída: pessoa, profissional e CNS (dados ilustrativos)'),
                ],
                'html': f'''
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
{{SHOT0}}
<p class="callout warning"><strong>IMPORTANTE:</strong> Administrador e gestor central enxergam a rede. Mesmo assim, ao registrar algo “da unidade”, confira o seletor — o registro nasce na unidade escolhida, não “na Secretaria inteira”.</p>
<h2>Meu perfil</h2>
<p>No canto superior direito, abra o seu nome e clique em <strong>Meu Perfil</strong>. Lá você:</p>
<ul>
<li>confere nome, e-mail e foto;</li>
<li>altera a senha (informe a senha atual e a nova);</li>
<li>vê unidades às quais está vinculado;</li>
<li>consulta, só para leitura, como o seu cadastro está no <strong>SIS</strong>, no <strong>CADSUS</strong> e no <strong>CNES</strong>.</li>
</ul>
<h3>Verificar dados de cadastro no SIS</h3>
<p>Role a tela de perfil até o cartão <strong>Cadastro no SIS</strong>, no final da página. Se o seu usuário no SIGUS já tem CPF, o botão <strong>Verificar dados de cadastro no SIS</strong> aparece. Clique e espere alguns segundos.</p>
{{SHOT1}}
<p>O sistema busca pessoa, operador, profissional, CADSUS, CNES e o cadastro de usuário do SIS. O resultado aparece em cartões, campo a campo. Nada disso grava de volta no SIGUS nem no SIS — é só para você conferir.</p>
{{SHOT2}}
{c('info', 'Só consulta:', 'Essa tela não altera o SIS e não trava nenhum campo do SIGUS. Se telefone, e-mail, conselho ou perfil no SIS estiver errado, abra um chamado para a coordenação ou a TI atualizar lá.')}
{c('warning', 'ATENÇÃO:', 'Sem CPF no cadastro do SIGUS a consulta não abre. Peça à coordenação para completar o seu usuário ou abra um chamado.')}
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
        'name': 'Dashboard, comunicados e mural',
        'description': 'O dia a dia da unidade: recados com ciência, mural de ações e o que aparece na tela inicial.',
        'pages': [
            {
                'name': 'O dashboard da unidade',
                'shots': [
                    ('dash', 'Dashboard da unidade: comunicados à esquerda e mural da rede à direita'),
                    ('dash-mural-foto', 'Foto do mural ampliada no lightbox, a partir do dashboard'),
                ],
                'html': '''
<p>Depois do login, o <strong>Dashboard</strong> mostra o dia a dia da <strong>unidade em que você está logado</strong> — não um painel genérico da rede inteira.</p>
{SHOT0}
<h2>O que tem na tela</h2>
<table>
<thead><tr><th>Bloco</th><th>Para que serve</th></tr></thead>
<tbody>
<tr><td>Aniversariantes hoje / do mês</td><td>Quem da unidade faz aniversário. Se for o seu dia, aparece um cartão de parabéns no alto.</td></tr>
<tr><td>Abonando hoje</td><td>Colegas com falta abonada neste dia — útil para a escala.</td></tr>
<tr><td>Comunicados da unidade</td><td>Recados oficiais. Se pedir ciência e você ainda não assinou, o cartão fica destacado e o botão <strong>Dar ciência</strong> aparece.</td></tr>
<tr><td>Chamados abertos</td><td>Pedidos de manutenção ainda em aberto da unidade.</td></tr>
<tr><td>Mural da rede</td><td>Ações locais (foto + recado curto) e itens da Lojinha Interna, com o status (disponível, pego, retirado).</td></tr>
</tbody>
</table>
<p>No computador, as duas colunas ocupam a altura da tela: a rolagem acontece <strong>dentro</strong> de cada cartão, não na página inteira. No celular os blocos empilham.</p>
<h2>Atalhos de quem publica</h2>
<p>Coordenação, apoio administrativo, gestor central e administrador veem no alto:</p>
<ul>
<li><strong>Novo comunicado</strong> — recado para a equipe, com ou sem ciência.</li>
<li><strong>Registrar ação</strong> — foto e texto curto para o mural.</li>
</ul>
<p>Clique numa miniatura do mural para ver a foto grande (dá para passar para a próxima, se houver mais de uma).</p>
{SHOT1}
<p class="callout info"><strong>Unidade no topo:</strong> se o seletor estiver em outra casa, você vê o dashboard dela. Confira antes de dar ciência ou de publicar.</p>
<p class="callout success"><strong>Dica:</strong> O mural completo, com filtro por unidade, tema e mês, fica em <strong>Ver tudo</strong> no cartão do mural.</p>
'''
            },
            {
                'name': 'Como publicar e dar ciência em um comunicado',
                'shots': [
                    ('com-novo', 'Formulário Novo comunicado: título, texto, busca de unidades, anexos e cobrar ciência'),
                    ('com-ciencia', 'Tela do comunicado com CPF, campo de assinatura e o botão Registrar ciência'),
                    ('com-imprimir', 'Termo de ciência no padrão SIGUS, com CPF anonimizado embaixo do nome'),
                ],
                'html': '''
<p>Comunicado é o recado oficial da unidade (ou da Secretaria, quando o gestor central compartilha). Não substitui e-mail nem o SISWEB: serve para a equipe <strong>ler e, se pedido, dar ciência</strong> com trilha de auditoria.</p>
<h2>Quem publica</h2>
<p>Apoio administrativo, coordenador, gestor central e administrador. Quem só opera a unidade lê e dá ciência; não cria comunicado.</p>
<h2>Como publicar</h2>
<ol>
<li>No dashboard, clique em <strong>Novo comunicado</strong>.</li>
<li>Escreva o <strong>título</strong> (obrigatório) e o texto, se quiser.</li>
<li>Anexe até 5 arquivos (PDF, Word ou imagem, 10 MB cada). Foto entra no impresso; o nome do arquivo sozinho não basta.</li>
<li>Marque <strong>Cobrar ciência de todo mundo com vínculo ativo nas unidades</strong> se o recado precisar de confirmação (é o padrão).</li>
<li>Clique em <strong>Publicar</strong>.</li>
</ol>
{SHOT0}
<p>Gestor central e administrador escolhem as unidades na lista, com <strong>busca em tempo real</strong> pelo nome. Coordenação e apoio administrativo publicam só na unidade do topo.</p>
<p class="callout warning"><strong>ATENÇÃO:</strong> Quem publica <strong>não ganha ciência automática</strong>. Se o comunicado cobra ciência e você também é destinatário, o sistema te leva para assinar — o autor assina igual a todo mundo.</p>
<h2>Como dar ciência</h2>
<p>Abra o comunicado (pelo dashboard, pelo sino ou pelo botão <strong>Dar ciência</strong>). Role até o bloco de ciência e:</p>
<ol>
<li>Digite o <strong>CPF cadastrado no SIGUS</strong> (máscara 000.000.000-00). Tem que ser o seu — o sistema confere com o cadastro.</li>
<li>Assine no quadro com o mouse ou o dedo (no tablet).</li>
<li>Clique em <strong>Registrar ciência</strong>.</li>
</ol>
{SHOT1}
<p class="callout warning"><strong>IMPORTANTE:</strong> Sem CPF no seu cadastro o SIGUS não registra a ciência. Peça à coordenação para completar o perfil. CPF de outra pessoa é recusado.</p>
<p>Ficam gravados: data e hora, IP, unidade em que você estava logado, origem (assinatura na tela) e a imagem da assinatura.</p>
<h2>Quem já assinou e o impresso</h2>
<p>Quem publica (e o autor) vê, à direita, quem ainda falta e quem já cientificou — com a assinatura. O botão <strong>Imprimir</strong> abre o modal padrão do SIGUS (logo da Prefeitura, termo de ciência).</p>
{SHOT2}
<p>No impresso, o <strong>CPF aparece anonimizado</strong> embaixo do nome, no formato da LGPD: <em>000.***.**0-00</em> (só o começo, o 9º dígito e os dois finais). A coluna <strong>Origem</strong> continua (assinatura na tela, autor na publicação etc.).</p>
<p class="callout info"><strong>LGPD:</strong> o CPF completo fica só no registro interno de auditoria. Papel e PDF da equipe não levam o número inteiro.</p>
<p class="callout success"><strong>Dica:</strong> Depois de assinar, o cartão no dashboard muda para <strong>Ciência ok</strong>. Se o recado não pedir ciência, não há o que assinar.</p>
'''
            },
            {
                'name': 'Mural de ações da rede',
                'shots': [
                    ('mural', 'Mural da rede com filtros de unidade, tema e mês'),
                    ('acao-nova', 'Formulário compacto Registrar ação: tema, data, descrição e fotos'),
                ],
                'html': '''
<p>O <strong>mural</strong> é o feed da rede: ações que a unidade registrou (educação em saúde, grupo, mutirão…) e também os itens anunciados na <strong>Lojinha Interna</strong>.</p>
{SHOT0}
<h2>Como registrar uma ação</h2>
<p>Quem publica (coordenação, apoio administrativo, gestor central, administrador):</p>
<ol>
<li>No dashboard, <strong>Registrar ação</strong> — ou, no mural, o mesmo botão.</li>
<li>Confira a unidade (gestor central e administrador podem escolher outra).</li>
<li>Escolha o <strong>tema</strong> (lista no padrão dos temas para saúde da Ficha de Atividade Coletiva do e-SUS APS).</li>
<li>Informe a data, um recado curto (até 400 caracteres) e de <strong>1 a 4 fotos</strong>.</li>
<li>Envie. A ação aparece no mural da rede e no cartão do dashboard.</li>
</ol>
{SHOT1}
<p>As fotos entram em miniatura. Clique para ampliar; se houver mais de uma, as setas (ou o dedo) passam de uma para a outra.</p>
<h2>Lojinha no mural</h2>
<p>Item anunciado na Lojinha Interna também entra no feed, com o status:</p>
<ul>
<li><strong>Disponível</strong> — ainda pode ser pedido.</li>
<li><strong>Pego</strong> — outra unidade já reservou.</li>
<li><strong>Retirado</strong> — saiu da vitrine.</li>
</ul>
<p>O atalho <strong>Ver lojinha</strong> abre a aba certa em Transferências. O passo a passo de anunciar e pegar item continua no capítulo de patrimônio deste livro.</p>
<h2>Filtros</h2>
<p>Em <strong>Ver tudo</strong> você filtra por unidade, tema (incluindo “Lojinha Interna”) e mês.</p>
<p class="callout info"><strong>Temas:</strong> a lista vive em <strong>Configurações → Tipos de ação (mural)</strong>. Dá para incluir tema novo ou desativar o que não se usa mais. Tema desativado some do formulário e permanece no histórico.</p>
<p class="callout success"><strong>Dica:</strong> O mural é compacto de propósito. Comunicado longo, com anexo e ciência, vai em <strong>Novo comunicado</strong> — não no registrar ação.</p>
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
                'shots': [
                    ('un-ficha', 'Ficha da unidade com as abas (Chamados, Segurança do Paciente, Equipamentos, Salas…)'),
                    ('un-ficha-chamados', 'Aba Chamados da ficha da unidade'),
                    ('un-ficha-info', 'Aba Informações da ficha da unidade'),
                ],
                'html': '''
<p>A ficha da unidade é a “capa” do serviço no SIGUS. Quase tudo que é da casa passa por ela.</p>
<h2>Como chegar</h2>
<ol>
<li>Confira a unidade padrão no topo.</li>
<li>No menu <strong>Gestão da Unidade</strong>, clique no nome da unidade (ou em <strong>Unidades</strong>, se você vê a lista da rede).</li>
<li>A ficha abre com várias abas.</li>
</ol>
{SHOT0}
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
{SHOT1}
<p class="callout info"><strong>Dica:</strong> Equipamento sem sala certa vira chamado e transferência confusos. Mantenha a aba de salas e a de equipamentos alinhadas com o que existe de verdade no prédio.</p>
<h2>Impressos do SIGUS</h2>
<p>Várias telas têm o botão <strong>Imprimir</strong>. No SIGUS o padrão é abrir um <strong>quadro (modal)</strong> com a pré-visualização do documento institucional (logo da Prefeitura, Secretaria da Saúde, campos e espaço para assinatura). De lá você escolhe <strong>Imprimir / Salvar PDF</strong>.</p>
{SHOT2}
<p class="callout success"><strong>Vale para:</strong> chamado, segurança do paciente, falta abonada, termo de transferência, planejamento, contrato e <strong>termo de ciência de comunicado</strong> — o visual é o mesmo padrão da casa.</p>
'''
            },
            {
                'name': 'Como abrir e acompanhar um chamado',
                'shots': [
                    ('ch-escolha', 'Tela Novo Chamado: escolha entre bem permanente, solicitação de equipamento ou predial'),
                    ('ch-predial', 'Formulário de chamado predial'),
                    ('ch-lista', 'Lista de chamados da unidade'),
                ],
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
{SHOT0}
<li>Preencha a descrição com o máximo de detalhe útil (o que acontece, desde quando, o que já tentaram).</li>
<li>Anexe foto ou vídeo, se ajudar o técnico (há limite de tamanho por arquivo).</li>
<li>Envie. O sistema gera um <strong>número de chamado</strong>.</li>
</ol>
{SHOT1}
<p class="callout warning"><strong>ATENÇÃO:</strong> Se o chamado é de um bem permanente, escolha o equipamento certo na lista. Chamado “solto”, sem patrimônio, atrasa o atendimento e confunde a transferência depois.</p>
<h2>Acompanhar</h2>
<p>Na mesma aba você vê status, prioridade e última atualização. Abrindo o chamado, há a linha do tempo (andamentos) e o botão de impressão no padrão SIGUS.</p>
{SHOT2}
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
                'shots': [('nsp-lista', 'Lista da Segurança do Paciente com totais, filtros, Nova notificação e consultar protocolo')],
                'html': '''
<p>O módulo <strong>Segurança do Paciente</strong> é o registro interno do <strong>Núcleo de Segurança do Paciente (NSP)</strong> da unidade. Serve para aprender com o que aconteceu e melhorar o cuidado — não para punir pessoas.</p>
<p>Base: RDC 36/2013, classificação da OMS (ICPS) e orientações da Anvisa. O SIGUS <strong>não envia nada para o Notivisa</strong>. Se a unidade notificar a Anvisa, você só anota o número e a data no registro.</p>
{SHOT0}
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
                'shots': [
                    ('nsp-nova', 'Formulário Nova notificação: notificante e pessoa afetada'),
                    ('nsp-nova-sis', 'Busca do paciente no SIS por CPF, CNS ou prontuário, com a opção de preencher na mão'),
                ],
                'html': '''
<p>Menu <strong>Gestão da Unidade → Segurança do Paciente → Nova notificação</strong> (ou o botão na aba da ficha da unidade).</p>
{SHOT0}
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
{SHOT1}
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
                'shots': [('nsp-detalhe', 'Ficha da notificação: registro, investigação, status, encaminhar e imprimir')],
                'html': '''
<p>Abra a notificação pelo protocolo na lista, pela consulta de protocolo ou pela aba da unidade.</p>
{SHOT0}
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
                'shots': [('plan', 'Tela Planejamentos e Projetos da unidade')],
                'html': '''
<p>O módulo de <strong>Planejamentos</strong> organiza projetos e ações da unidade em formato de quadro (colunas de status), com priorização.</p>
{SHOT0}
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
                'shots': [('agenda', 'Agenda da unidade com calendário, Novo evento e Nova reunião')],
                'html': '''
<p>A <strong>Agenda</strong> junta, no mesmo calendário:</p>
<ul>
<li>compromissos e eventos da unidade;</li>
<li>reuniões (com lista de participantes, quando for o caso);</li>
<li>prazos de planejamentos;</li>
<li>feriados cadastrados pela administração (com expediente especial, se houver).</li>
</ul>
{SHOT0}
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
                'shots': [('ch-gestao', 'Fila Gestão de Chamados com totais por status')],
                'html': '''
<p>A tela <strong>Operações → Gestão de Chamados</strong> é a fila de quem <strong>executa</strong> o serviço (manutenção da unidade que trata aquele tipo de chamado), não a lista de quem só abriu o pedido.</p>
{SHOT0}
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
                'shots': [('tr-lista', 'Tela Transferências de Equipamentos, com as abas e o botão Novo Termo')],
                'html': '''
<p>Quando um bem permanente precisa mudar de unidade (ou de local), use <strong>Operações → Transferências</strong>. Não “apague” o equipamento de uma lista e cadastre de novo na outra: o histórico patrimonial se perde.</p>
{SHOT0}
<ol>
<li>Abra <strong>Novo Termo</strong> (ou <strong>Transferir</strong> na ficha do bem).</li>
<li>Informe origem, destino e os itens (do inventário ou manuais).</li>
<li>A unidade de destino <strong>aceita</strong> o termo e escolhe a <strong>sala</strong> — ou recusa.</li>
<li>Imprima o termo pelo modal do SIGUS e colete as assinaturas.</li>
</ol>
<h2>Quem atualiza inventário da rede (administrador e gestor central)</h2>
<p>Esses dois perfis escolhem <strong>qualquer unidade de origem e qualquer destino</strong>, mesmo com outra unidade no seletor do topo. Ao selecionar as unidades, o SIGUS lista o inventário de cada uma. Depois de criar o termo, a <strong>mesma pessoa</strong> cai na tela de aceite, escolhe a sala do prédio novo e conclui — não precisa esperar o coordenador da ponta nem trocar a unidade do cabeçalho.</p>
<p>Coordenador e apoio administrativo continuam só com as unidades vinculadas: origem no topo, aceite em nome da unidade destino selecionada.</p>
<p class="callout info"><strong>Dica:</strong> Conferir número de patrimônio e sala antes de enviar evita aceite de item errado. O passo a passo tela a tela (pendentes, novo termo, aceite, lojinha) está no capítulo <strong>Patrimônio: salas, equipamentos, transferências e lojinha</strong> deste mesmo livro.</p>
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
                'shots': [
                    ('faltas', 'Tela Faltas Abonadas com o botão Nova Falta Abonada'),
                    ('faltas-modal', 'Modal para registrar uma nova falta abonada'),
                ],
                'html': '''
<p>Servidores estatutários têm direito a <strong>6 faltas abonadas no ano</strong>, no máximo <strong>1 por mês</strong>. O SIGUS controla esse limite para o seu usuário.</p>
{SHOT0}
<h2>Como registrar</h2>
<ol>
<li>Menu <strong>Recursos Humanos → Faltas Abonadas</strong>.</li>
<li>Clique em <strong>Nova Falta Abonada</strong>.</li>
<li>Escolha a data (o calendário já bloqueia mês em que você já usou abonada ativa).</li>
<li>Informe função e unidade, se o sistema pedir.</li>
<li>Salve e imprima o documento pelo modal (padrão institucional, para a chefia).</li>
</ol>
{SHOT1}
<p class="callout warning"><strong>ATENÇÃO:</strong> A abonada deve ser combinada com a chefia com antecedência (regra da casa: em geral 2 dias úteis). O SIGUS registra o pedido; a autorização da escala continua sendo da chefia. Cargo de confiança segue a legislação específica — nem todo mundo acumula abonada para pagamento.</p>
<p>Abonadas canceladas não contam no limite do ano e aparecem no histórico. Quem gerencia usuários pode ver a ficha de outra pessoa; o operador padrão vê a própria.</p>
'''
            },
            {
                'name': 'Cadastro público e vínculo na unidade',
                'shots': [('vinculo', 'Formulário público de solicitação de vínculo profissional, sem precisar estar logado')],
                'html': '''
<p>Profissional que ainda não tem usuário no SIGUS pode pedir vínculo pelo formulário público (<strong>solicitar vínculo profissional</strong>). Não precisa estar logado.</p>
{SHOT0}
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
        'description': 'Exportar dados, contratos, cadastro de usuários (importação SIS) e o que a unidade vê nos selects.',
        'pages': [
            {
                'name': 'Relatórios e exportação',
                'shots': [('relatorios', 'Tela Relatórios e Inventários com os cartões de cada relatório')],
                'html': '''
<p>Menu <strong>Gestão da Unidade → Relatórios</strong>. A tela inicial é um conjunto de cartões. Cada relatório traz filtro (unidade, período, status, conforme o tema) e exportação em Excel ou CSV.</p>
{SHOT0}
<p>Exemplos: inventário, salas, profissionais, contratos, empenhos, aniversariantes, faltas abonadas, <strong>segurança do paciente</strong>, mapa da saúde.</p>
<p class="callout info"><strong>Permissão:</strong> quem não vê todas as unidades só exporta o que pode ver. Isso é regra de segurança, não filtro “quebrado”.</p>
'''
            },
            {
                'name': 'Contratos, empenho e empresas',
                'shots': [('contratos', 'Lista de Contratos em Gestão Financeira')],
                'html': '''
<p>Essas telas ficam em <strong>Gestão Financeira</strong> e só aparecem para quem tem permissão.</p>
{SHOT0}
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
                'shots': [
                    ('cfg', 'Tela Configurações do Sistema, com os cartões (feriados, unidades, perfis…)'),
                    ('cfg-perfis', 'Gestão de Perfis: Ver / Editar / Adicionar por seção'),
                    ('cfg-nsp', 'Listas da Segurança do Paciente usadas nos selects da notificação'),
                    ('cfg-identidade', 'Identidade da instalação: textos do município e galeria de logos, favicon e brasão'),
                    ('cfg-tipos', 'Tipos de ação do mural, no padrão dos temas para saúde do e-SUS APS'),
                ],
                'html': '''
<p>Área sensível. Em geral é da Saúde Digital / administração do sistema, com apoio da coordenação.</p>
{SHOT0}
<h2>Gestão de perfis</h2>
<p>Em <strong>Configurações → Gestão de Perfis</strong> cada perfil ganha Ver / Editar / Adicionar por seção. Mudar aqui altera o menu de todo mundo daquele perfil.</p>
{SHOT1}
<p class="callout warning"><strong>ATENÇÃO:</strong> Não “teste” permissão em produção no perfil de toda a rede. Ajuste com cuidado e comunique a coordenação.</p>
<h2>Listas da Segurança do Paciente</h2>
<p>Os selects da notificação (status, classificação, tipo de incidente, setor, destino…) não estão fixos no código. Inclua, desative ou marque “pede texto Outro” e “jamais deveria ocorrer” em <strong>Configurações → Segurança do Paciente</strong>. Item desativado some dos formulários novos e permanece no histórico antigo.</p>
{SHOT2}
<h2>Identidade da instalação</h2>
<p>Em <strong>Configurações → Identidade e assets</strong> (só administrador) ficam município, secretaria, domínio de e-mail e as imagens do login, da barra lateral e dos impressos (logo, favicon, brasão). Sem arquivo enviado, vale o padrão de Sorocaba. A paleta de cores do SIGUS não muda nesta tela.</p>
{SHOT3}
<h2>Tipos de ação (mural)</h2>
<p>Os temas do mural seguem a Ficha de Atividade Coletiva do e-SUS APS e podem ganhar item novo ou ser desativados em <strong>Configurações → Tipos de ação (mural)</strong>.</p>
{SHOT4}
<h2>Feriados, usuários, links úteis</h2>
<p>Feriados alimentam a agenda. Links úteis: atalhos que a equipe vê no menu da unidade.</p>
<p>O cadastro de usuários (alta, importação do SIS, matrícula e conselho de classe) está no passo a passo <strong>Cadastro de usuários no SIGUS</strong>, neste mesmo capítulo — é a rotina de quem administra o sistema.</p>
<h2>Auditoria</h2>
<p>Quase toda ação relevante (login, alteração, exclusão) pode ser consultada em <strong>Configurações → Auditoria</strong>, por quem tiver permissão. Por isso o login precisa ser individual.</p>
'''
            },
            {
                'name': 'Cadastro de usuários no SIGUS',
                'shots': [
                    ('usr-lista', 'Menu Configurações aberto no item Usuários e lista com busca e botão Novo Usuário'),
                    ('usr-novo-acesso', 'Aba Acesso do cadastro novo: CPF na frente e botão Importar dados cadastrais'),
                    ('usr-novo-importado', 'Depois da importação: mensagem de sucesso e campos preenchidos, ainda editáveis'),
                    ('usr-novo-pessoal', 'Aba Dados Pessoais: CNS, Localizar no CNES, filiação, RG e nascimento'),
                    ('usr-novo-endereco', 'Aba Endereço preenchida com o cadastro de usuário do SIS'),
                    ('usr-matriculas', 'Aba Matrículas depois que o usuário já existe, com Adicionar Matrícula'),
                    ('usr-matricula-modal', 'Modal de nova matrícula com Consultar conselho no SIS'),
                ],
                'html': f'''
<p>Esta página é para quem <strong>cadastra e edita usuários</strong> no SIGUS — administrador, gestor central e quem tiver a permissão de cadastrar usuário. O profissional da ponta não usa esta tela no dia a dia.</p>
<h2>Onde fica</h2>
<p>No menu da esquerda: <strong>Configurações → Usuários</strong>. Se o grupo Configurações estiver fechado, clique no título para abrir. Se o item não aparecer, o seu perfil não tem permissão — peça a um administrador.</p>
<p>A lista traz nome, e-mail, WhatsApp, perfil, matrícula/CBO e se o usuário está ativo. A busca (nome ou parte do e-mail) atualiza sozinha depois que você para de digitar. O botão <strong>Novo Usuário</strong> fica no alto, à direita.</p>
{{SHOT0}}
<h2>Como criar um usuário (passo a passo)</h2>
<ol>
<li>Clique em <strong>Novo Usuário</strong>.</li>
<li>Você cai na aba <strong>Acesso</strong>. O <strong>primeiro campo é o CPF</strong> — não comece pelo nome.</li>
<li>Digite o CPF (com ou sem pontuação: <em>000.000.000-00</em> ou só os 11 dígitos).</li>
<li>Clique no botão azul <strong>Importar dados cadastrais</strong>, ao lado do CPF.</li>
</ol>
{{SHOT1}}
<p>Espere alguns segundos. Uma mensagem verde confirma quantos campos vieram. O SIGUS consulta, nesta ordem, o que existir:</p>
<ul>
<li>cadastro de <strong>pessoa</strong> no SIS — nome, mãe, pai, RG, escolaridade, nascimento;</li>
<li><strong>CADSUS</strong> — útil quando a pessoa ainda não está no SIS;</li>
<li>cadastro de <strong>profissional</strong> e de <strong>operador</strong> no SIS — e-mail, conselho, login;</li>
<li>cadastro de <strong>usuário</strong> no SIS — <strong>endereço e telefone mandam</strong> (é o que a ponta costuma manter atualizado);</li>
<li><strong>CNES</strong> — CNS do profissional (o número “de verdade” do DATASUS, não o CNS provisório do CADSUS).</li>
</ul>
{{SHOT2}}
<ol start="5">
<li>Olhe as abas <strong>Dados Pessoais</strong> e <strong>Endereço</strong>. Nada fica travado: se um campo veio errado ou vazio, você corrige na mão.</li>
<li>Na aba Acesso, escolha o <strong>perfil de acesso</strong> e complete o e-mail se a importação não trouxe (pode ser só a parte antes do @).</li>
<li>Clique em <strong>Criar Usuário</strong>.</li>
</ol>
{c('info', 'Senha inicial:', 'A senha de quem acaba de ser criado é o CPF <strong>só com os dígitos</strong>, sem pontos nem traço. A pessoa troca em Meu Perfil no primeiro acesso. Avise isso na hora de entregar o login.')}
{c('success', 'Dica:', 'Se o SIS não tiver a pessoa, o CADSUS e o CNES ainda podem preencher nome, filiação, endereço e CNS. Se nenhuma base achar o CPF, preencha na mão — o usuário nasce do mesmo jeito.')}
{c('warning', 'ATENÇÃO:', 'A importação só lê. O SIGUS não grava nada no SIS, no CADSUS nem no CNES. Dado importado não significa dado conferido: olhe nome, e-mail e CPF antes de criar.')}
<h2>Aba Dados pessoais</h2>
<p>Aqui entram CNS, filiação, sexo, nascimento, RG, escolaridade e nacionalidade. O botão <strong>Localizar no CNES</strong> abre o site do DATASUS numa nova aba, para você conferir na fonte se quiser. Ele não grava sozinho — copie o que precisar.</p>
{{SHOT3}}
<h2>Aba Endereço</h2>
<p>Logradouro, número, bairro, município, UF, CEP, telefone e WhatsApp. Quando existe cadastro de usuário no SIS, o endereço vem de lá. Se a ponta atualizou o telefone no SIS e o SIGUS ainda está velho, importe de novo (o botão também funciona na edição).</p>
{{SHOT4}}
<h2>Aba Matrículas (depois de criar)</h2>
<p>Essa aba <strong>só aparece depois</strong> que o usuário já existe. Cada matrícula é um vínculo empregatício (estatutário, contrato, residência, estágio), com CBO e conselho de classe. Sem matrícula, o vínculo com a unidade fica incompleto.</p>
{{SHOT5}}
<h2>Conselho de classe na matrícula</h2>
<ol>
<li>Abra o usuário → aba <strong>Matrículas</strong> → <strong>Adicionar Matrícula</strong>.</li>
<li>Preencha vínculo, tipo e, se for o caso, o número da matrícula.</li>
<li>Clique em <strong>Consultar conselho no SIS</strong>. O SIGUS usa o CPF da aba Acesso e busca o cadastro de profissional.</li>
<li><strong>Nenhum encontrado</strong> — o sistema avisa para preencher órgão e número na mão.</li>
<li><strong>Um encontrado</strong> — preenche órgão (ex.: COREN-SP) e número. Você ainda pode alterar.</li>
<li><strong>Mais de um</strong> — abre um modal para você escolher qual conselho entra nesta matrícula.</li>
</ol>
{{SHOT6}}
{c('info', 'Campos com *:', 'Nome e e-mail são obrigatórios para criar o usuário. Número da matrícula é obrigatório no modal, salvo contrato por prazo determinado (aí pode ficar “Sem Matrícula”).')}
{c('success', 'Dica:', 'O próprio profissional pode conferir o cadastro no SIS em Meu Perfil → Verificar dados de cadastro no SIS. Se algo estiver desatualizado lá, oriente a abrir um chamado — o SIGUS não corrige o SIS.')}
'''
            },
        ],
    },
]


PAGES_SOMENTE_NOTICIAS = {
    'O que é o SIGUS',
    'O dashboard da unidade',
    'Como publicar e dar ciência em um comunicado',
    'Mural de ações da rede',
    'Como abrir a ficha da unidade',
    'Configurações, perfis e auditoria',
}


def chapters_para_publicar(somente_noticias: bool):
    if not somente_noticias:
        return CHAPTERS
    out = []
    for ch in CHAPTERS:
        pages = [p for p in ch['pages'] if p['name'] in PAGES_SOMENTE_NOTICIAS]
        if pages:
            item = dict(ch)
            item['pages'] = pages
            out.append(item)
    return out


def publish(s: requests.Session, chapters=None) -> None:
    chapters = chapters or CHAPTERS
    api(s, 'PUT', f'/books/{BOOK_ID}', json={
        'name': 'Manuais de utilização do SIGUS',
        'description_html': BOOK_DESC,
    })
    print('Livro atualizado (descrição).')

    existing = api(s, 'GET', f'/books/{BOOK_ID}')
    already = {c['name']: c for c in existing.get('contents', []) if c.get('type') == 'chapter'}

    for i, ch in enumerate(chapters, start=1):
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
            html = pg['html']
            shots = pg.get('shots') or []
            payload_html = strip_shot_placeholders(html) if shots else html
            if pg['name'] in pages_exist:
                pid = pages_exist[pg['name']]['id']
                api(s, 'PUT', f'/pages/{pid}', json={'name': pg['name'], 'html': payload_html})
                print(f'  página atualizada: {pg["name"]}')
            else:
                created = api(s, 'POST', '/pages', json={
                    'chapter_id': cid,
                    'name': pg['name'],
                    'html': payload_html,
                    'priority': j,
                })
                pid = created['id']
                pages_exist[pg['name']] = {'id': pid}
                print(f'  página criada: {pg["name"]} -> {created.get("url") or created.get("slug")}')
            if shots:
                for idx, (stem, alt) in enumerate(shots):
                    print(f'    print {stem}...')
                    html = html.replace(f'{{SHOT{idx}}}', upload_shot(s, pid, stem, alt))
                api(s, 'PUT', f'/pages/{pid}', json={'name': pg['name'], 'html': html})
                print(f'    html+prints ok')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--somente-noticias',
        action='store_true',
        help='Atualiza dashboard, comunicados, mural e páginas ligadas.',
    )
    args = parser.parse_args()
    chapters = chapters_para_publicar(args.somente_noticias)
    missing = [
        stem
        for ch in chapters
        for pg in ch['pages']
        for stem, _alt in (pg.get('shots') or [])
        if not (SHOT / f'{stem}.png').exists()
    ]
    if missing:
        print('Prints faltando:', ', '.join(missing))
        sys.exit(1)
    s = session_login()
    publish(s, chapters)
    print('OK. Abra', f'{BASE}/books/manuais-de-utilizacao-do-sigus')


if __name__ == '__main__':
    main()
