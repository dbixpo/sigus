# -*- coding: utf-8 -*-
"""O que cada requisição vira na tabela de auditoria.

O gancho em create_app chama estas funções. A notificação de Segurança
do Paciente continua sem usuário, IP e parâmetros.
"""

ACAO_LABELS = {
    'view': 'Consulta',
    'search': 'Pesquisa',
    'create': 'Inclusão',
    'update': 'Alteração',
    'delete': 'Exclusão',
    'export': 'Exportação',
    'print': 'Impressão',
    'login': 'Login',
    'logout': 'Saída',
}

MODULO_LABELS = {
    'agenda': 'Agenda',
    'auth': 'Acesso',
    'chamados': 'Chamados',
    'chamados_externo': 'Chamado sem login',
    'configuracoes': 'Configurações',
    'contrato_financeiro': 'Controle de empenho',
    'contratos': 'Contratos',
    'dashboard': 'Painel',
    'desconhecido': 'Endereço não encontrado',
    'empresas': 'Empresas',
    'equipamentos': 'Equipamentos',
    'frequencia': 'Apontamentos',
    'links': 'Links úteis',
    'mapa_da_saude': 'Mapa da Saúde',
    'noticias': 'Mural e comunicados',
    'notificacoes': 'Notificações',
    'nsp': 'Segurança do Paciente',
    'planejamentos': 'Planejamentos',
    'predios': 'Prédios',
    'relatorios': 'Relatórios',
    'rh': 'Faltas abonadas',
    'salas': 'Salas',
    'sistema': 'Sistema',
    'solicitacoes': 'Cadastro público',
    'sueq': 'SUEQ',
    'transferencias': 'Transferências',
    'unidades': 'Unidades',
    'usuarios': 'Usuários',
    'veiculos': 'Veículos',
}

# Consultas automáticas do navegador. Não são uma ação de alguém na tela.
SEM_REGISTRO = {
    'static',
    'manifest',
    'notificacoes.recentes',
    'notificacoes.contagem',
}

_CHAVES_OMITIR = (
    'senha', 'password', 'csrf', 'token', 'secret', 'foto', 'imagem',
)

_CRIAR = (
    'novo', 'nova', 'criar', 'adicion', 'importar', 'publicar',
    'cadastr', 'registrar', 'abrir',
)
_EXCLUIR = ('excluir', 'remover', 'apagar', 'delete')
_EXPORTAR = ('export', 'xlsx', 'xls', 'csv', 'ods', 'planilha', 'baixar')
_ARGS_DE_PAGINA = {'page', 'per_page', 'pagina'}


def deve_registrar(endpoint):
    return endpoint not in SEM_REGISTRO


def modulo_de(endpoint):
    if not endpoint:
        return 'desconhecido'
    if endpoint.startswith('mapa_da_saude'):
        return 'mapa_da_saude'
    if endpoint.startswith('redirect_') or endpoint == 'manifest':
        return 'sistema'
    if '.' in endpoint:
        return endpoint.split('.')[0]
    return endpoint


def rotulo_modulo(codigo):
    return MODULO_LABELS.get(codigo, codigo or '—')


def classificar_acao(endpoint, method, url, chaves_args=()):
    ep = (endpoint or '').lower()
    caminho = (url or '').lower()
    texto = ep + ' ' + caminho
    metodo = (method or 'GET').upper()
    if ep == 'auth.login' and metodo == 'POST':
        return 'login'
    if ep == 'auth.logout':
        return 'logout'
    if metodo == 'GET':
        if any(p in texto for p in _EXPORTAR):
            return 'export'
        if 'imprimir' in ep or '/imprimir' in caminho:
            return 'print'
        uteis = [c for c in chaves_args if c not in _ARGS_DE_PAGINA]
        if uteis:
            return 'search'
        return 'view'
    if metodo == 'DELETE' or any(p in texto for p in _EXCLUIR):
        return 'delete'
    if any(p in texto for p in _CRIAR):
        return 'create'
    if any(p in texto for p in _EXPORTAR):
        return 'export'
    return 'update'


def ip_cliente(request):
    ip = (request.remote_addr or '').strip()
    if ip in ('', '127.0.0.1', '::1'):
        encaminhado = (request.headers.get('X-Forwarded-For') or '').split(',')[0].strip()
        if encaminhado:
            ip = encaminhado
    return ip[:45] if ip else None


def _limpar_valor(chave, valor):
    nome = (chave or '').lower()
    if any(pedaco in nome for pedaco in _CHAVES_OMITIR):
        return '[omitido]'
    if isinstance(valor, (list, tuple)):
        texto = ', '.join(str(v) for v in valor[:12])
    elif isinstance(valor, dict):
        texto = ', '.join(f'{k}' for k in list(valor)[:12])
    else:
        texto = '' if valor is None else str(valor)
    if len(texto) > 300:
        return f'[texto de {len(texto)} caracteres]'
    return texto


def _bloco(itens, limite=40):
    saida = {}
    for chave, valor in list(itens)[:limite]:
        saida[str(chave)[:80]] = _limpar_valor(str(chave), valor)
    return saida


def parametros_da_requisicao(request, anonima=False):
    if anonima:
        return None
    saida = {}
    if request.args:
        saida['args'] = _bloco(request.args.items(multi=True))
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        if request.form:
            saida['form'] = _bloco(request.form.items(multi=True))
        arquivos = {}
        for chave, arquivo in request.files.items():
            nome = (getattr(arquivo, 'filename', None) or '').strip()
            if nome:
                arquivos[str(chave)[:80]] = nome[:120]
        if arquivos:
            saida['arquivos'] = arquivos
        if request.is_json:
            corpo = request.get_json(silent=True)
            if isinstance(corpo, dict):
                saida['json'] = _bloco(corpo.items())
    return saida or None


def extrair_entidade(request, modulo):
    args = request.view_args or {}
    preferidas = ('id', 'equipamento_id', 'unidade_id', 'plano_id', 'usuario_id')
    chaves = [c for c in preferidas if c in args] + [
        c for c in args if str(c).endswith('_id') and c not in preferidas
    ]
    for chave in chaves:
        try:
            return modulo, int(args[chave])
        except (TypeError, ValueError):
            continue
    return None, None


def resumo_parametros(parametros, limite=220):
    """Uma linha legível. Não devolve foto, senha nem texto enorme."""
    if not isinstance(parametros, dict):
        return ''
    partes = []
    for origem in ('form', 'json', 'args', 'arquivos'):
        bloco = parametros.get(origem)
        if not isinstance(bloco, dict):
            continue
        for chave, valor in bloco.items():
            if chave.lower() in _ARGS_DE_PAGINA:
                continue
            texto = _limpar_valor(chave, valor)
            if len(texto) > 60:
                texto = texto[:57] + '…'
            partes.append(f'{chave}: {texto}')
            if len(partes) >= 8:
                break
    return '; '.join(partes)[:limite]


def gravar_auditoria(request, current_user, response_status, exc, endpoints_anonimos):
    """Grava uma linha. Falha aqui não desfaz o que a tela já salvou."""
    from flask import g
    from app import db
    from app.models.auditoria import Auditoria

    endpoint = request.endpoint
    if not deve_registrar(endpoint):
        g._auditoria_done = True
        return
    # 404 anônimo de varredura não entra. 404 de quem está logado entra.
    if endpoint is None and not getattr(current_user, 'is_authenticated', False):
        if (request.method or 'GET').upper() == 'GET':
            g._auditoria_done = True
            return

    anonima = endpoint in endpoints_anonimos
    if anonima:
        rota = str(request.url_rule) if request.url_rule else request.path
        usuario_id, ip, user_agent, url = None, None, None, (rota or '')[:500]
    else:
        usuario_id = current_user.id if getattr(current_user, 'is_authenticated', False) else None
        ip = ip_cliente(request)
        user_agent = (request.headers.get('User-Agent') or '')[:500] or None
        url = (request.url or '')[:500]

    modulo = modulo_de(endpoint)
    tipo, entidade = extrair_entidade(request, modulo)
    try:
        db.session.add(Auditoria(
            usuario_id=usuario_id,
            acao=classificar_acao(endpoint, request.method, request.path, request.args.keys()),
            modulo=modulo,
            endpoint=(endpoint or request.path or '')[:200],
            url=url,
            method=(request.method or '')[:10],
            parametros=parametros_da_requisicao(request, anonima=anonima),
            entity_type=tipo,
            entity_id=entidade,
            ip_address=ip,
            user_agent=user_agent,
            response_status=response_status if response_status is not None else (500 if exc else None),
            detalhes=(str(exc)[:2000] if exc else None),
        ))
        db.session.commit()
        g._auditoria_done = True
    except Exception:
        db.session.rollback()
