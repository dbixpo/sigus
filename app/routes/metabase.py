# -*- coding: utf-8 -*-
"""Painéis do Metabase e pedido de acesso (chamado administrativo)."""
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import Blueprint, Response, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user

from app import csrf, db
from app.models.cbo import CBO
from app.models.chamado import Chamado, ChamadoHistorico, prioridade_de_gut
from app.models.link_util import PERFIS_LINK
from app.models.metabase import (
    MetabaseConfig, MetabasePainel, cbo_na_unidade, interpretar_codigo_metabase,
    rotulo_cbo,
)
from app.models.tipo_unidade import TipoUnidade
from app.models.unidade import Unidade
from app.models.usuario import PERFIS

metabase_bp = Blueprint('metabase', __name__, url_prefix='/metabase')

_INTERVALO_MIN = 10
_INTERVALO_MAX = 600
_METABASE_INTERNO = 'http://127.0.0.1:3000/'
_LIMITE_CORPO = 26 * 1024 * 1024
_CAMINHO_PONTE = re.compile(
    r'^(?:app/(?:dist|assets)/.+|embed/dashboard/\d+(?:/.*)?|api/embed/.+)$'
)
_PAINEL_PONTE = re.compile(r'^(?P<api>api/)?embed/dashboard/(?P<id>\d+)(?P<resto>/.*)?$')


def _pode_ver():
    return current_user.pode('ver_metabase')


def _pode_gerir():
    return current_user.pode('editar_metabase') or current_user.pode('adicionar_metabase')


def _config():
    cfg = MetabaseConfig.query.get(1)
    if cfg:
        return cfg
    cfg = MetabaseConfig(id=1, site_url='', secret_key='', intervalo_segundos=40)
    db.session.add(cfg)
    db.session.commit()
    return cfg


def _paineis_visiveis():
    itens = (MetabasePainel.query
             .filter_by(ativo=True)
             .order_by(MetabasePainel.ordem, MetabasePainel.id)
             .all())
    return [p for p in itens if p.visivel_para(current_user)]


def _unidade_saude_digital():
    ativas = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    for unidade in ativas:
        if (unidade.nome or '').strip().casefold() == 'saúde digital':
            return unidade
    for unidade in Unidade.que_tratam_tipo('solicitacao_administrativa'):
        nome = (unidade.nome or '').casefold()
        if 'saúde digital' in nome or 'saude digital' in nome:
            return unidade
    return None


def _unidade_da_pessoa():
    unidade = current_user.unidade_logada
    if unidade:
        return unidade
    ativas = current_user.unidades_ativas
    return ativas[0] if ativas else None


def _ler_painel(item):
    nome = (request.form.get('nome') or '').strip()
    if not nome:
        return None, 'Informe o nome do painel.'
    codigo = (request.form.get('codigo_secret') or '').strip()
    if codigo:
        lido, erro_codigo = interpretar_codigo_metabase(codigo)
        if erro_codigo:
            return None, erro_codigo
        resource_id = lido['resource_id']
        embedding = lido['embedding_params']
        params = lido['params']
        titled = lido['titled'] if lido['titled'] is not None else request.form.get('titled') == 'on'
    else:
        try:
            resource_id = int(request.form.get('resource_id') or 0)
        except (TypeError, ValueError):
            resource_id = 0
        if resource_id < 1:
            return None, 'Informe o número do dashboard ou cole o Python do Metabase.'
        embedding = {}
        params = {}
        titled = request.form.get('titled') == 'on'
    iniciais = {}
    perfis = request.form.getlist('perfis_acesso') or ['todos']
    if request.form.get('tipos_todos') == '1':
        tipos = []
    else:
        tipos = []
        for bruto in request.form.getlist('tipos_unidade_ids'):
            try:
                tipos.append(int(bruto))
            except (TypeError, ValueError):
                continue
    cbos = [c.strip() for c in request.form.getlist('cbos') if c.strip()]
    dados = {
        'nome': nome[:150],
        'descricao': (request.form.get('descricao') or '').strip()[:300] or None,
        'resource_id': resource_id,
        'bordered': request.form.get('bordered') == 'on',
        'titled': titled,
        'with_downloads': False,
        'embedding_params': embedding,
        'initial_parameters': iniciais,
        'params': params,
        'ativo': request.form.get('ativo') == 'on',
        'perfis_acesso': perfis,
        'tipos_unidade_ids': tipos,
        'cbos': cbos,
    }
    return dados, None


def _cartao(painel, _config):
    return {
        'id': painel.id,
        'nome': painel.nome,
        'descricao': painel.descricao or '',
        'bordered': bool(painel.bordered),
        'with_title': bool(painel.titled),
        'with_downloads': bool(painel.with_downloads),
        'initial_parameters': painel.initial_parameters if isinstance(painel.initial_parameters, dict) else {},
        'quadro': url_for('metabase.ponte', caminho=f'embed/dashboard/{painel.id}'),
    }


def _opcoes_form():
    return {
        'perfis': PERFIS_LINK,
        'tipos_unidade': TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all(),
        'cbos': CBO.query.filter_by(ativo=True).order_by(CBO.codigo).all(),
    }


@metabase_bp.route('/')
@login_required
def index():
    if not _pode_ver():
        abort(403)
    cfg = _config()
    visiveis = _paineis_visiveis() if cfg.pronta else []
    cartoes = []
    if cfg.pronta:
        cartoes = [_cartao(painel, cfg) for painel in visiveis]
    return render_template(
        'metabase/index.html',
        config=cfg,
        cartoes=cartoes,
        pode_configurar=_pode_gerir(),
    )


@metabase_bp.route('/paineis/<int:id>/endereco')
@login_required
def endereco(id):
    if not _pode_ver():
        abort(403)
    cfg = _config()
    if not cfg.pronta:
        abort(404)
    painel = MetabasePainel.query.get_or_404(id)
    if not painel.visivel_para(current_user):
        abort(403)
    resp = jsonify(_cartao(painel, cfg))
    resp.headers['Cache-Control'] = 'no-store'
    return resp


def _caminho_da_ponte(caminho):
    if not caminho or caminho.startswith(('/', '\\')) or '\\' in caminho:
        return None
    if any(parte == '..' for parte in caminho.split('/')):
        return None
    if not _CAMINHO_PONTE.match(caminho):
        return None
    return caminho


def _url_interna(caminho, token):
    destino = caminho
    achado = _PAINEL_PONTE.match(caminho)
    if achado and token:
        api = achado.group('api') or ''
        resto = achado.group('resto') or ''
        destino = f'{api}embed/dashboard/{token}{resto}'
    partes = '/'.join(quote(parte, safe='') for parte in destino.split('/'))
    url = _METABASE_INTERNO + partes
    consulta = request.query_string
    if consulta:
        url += '?' + consulta.decode('ascii', 'ignore')
    return url


@metabase_bp.route('/ponte/<path:caminho>', methods=['GET', 'HEAD', 'POST'])
@csrf.exempt
@login_required
def ponte(caminho):
    """O navegador pede o painel pelo número. O token comprido só vai até o Metabase local."""
    if not _pode_ver():
        abort(403)
    caminho = _caminho_da_ponte(caminho)
    if not caminho:
        abort(404)
    cfg = _config()
    if not cfg.pronta:
        abort(404)
    achado = _PAINEL_PONTE.match(caminho)
    painel = None
    token = None
    if achado:
        painel = db.session.get(MetabasePainel, int(achado.group('id')))
        if not painel or not painel.ativo:
            abort(404)
        if not painel.visivel_para(current_user):
            abort(403)
        token, _expira = painel.emitir_token(cfg)
    if request.method == 'POST' and (request.content_length or 0) > 2_000_000:
        abort(413)
    corpo = request.get_data() if request.method == 'POST' else None
    pedido = Request(_url_interna(caminho, token), data=corpo, method=request.method)
    tipo_pedido = request.headers.get('Content-Type')
    if tipo_pedido:
        pedido.add_header('Content-Type', tipo_pedido)
    aceita = request.headers.get('Accept')
    if aceita:
        pedido.add_header('Accept', aceita)
    try:
        upstream = urlopen(pedido, timeout=45)
    except HTTPError as exc:
        upstream = exc
    except URLError:
        return Response(
            'O Metabase não respondeu.',
            status=502,
            mimetype='text/plain; charset=utf-8',
        )
    try:
        bruto = upstream.read(_LIMITE_CORPO + 1)
    finally:
        upstream.close()
    if len(bruto) > _LIMITE_CORPO:
        return Response(
            'A resposta do Metabase veio grande demais.',
            status=502,
            mimetype='text/plain; charset=utf-8',
        )
    if token:
        bruto = bruto.replace(token.encode('ascii'), str(painel.id).encode('ascii'))
    resp = Response(bruto, status=getattr(upstream, 'status', None) or upstream.code)
    resp.headers['Content-Type'] = upstream.headers.get('Content-Type', 'application/octet-stream')
    if caminho.startswith('app/'):
        resp.headers['Cache-Control'] = 'public, max-age=86400'
    else:
        resp.headers['Cache-Control'] = 'no-store'
    politica = upstream.headers.get('Content-Security-Policy')
    if politica:
        resp.headers['Content-Security-Policy'] = politica
    return resp


@metabase_bp.route('/pedir-acesso', methods=['POST'])
@login_required
def pedir_acesso():
    if not _pode_ver():
        abort(403)
    justificativa = (request.form.get('justificativa') or '').strip()
    if len(justificativa) < 10:
        flash('Escreva a justificativa com pelo menos 10 caracteres.', 'warning')
        return redirect(url_for('metabase.index'))

    aberto = (Chamado.query
              .filter(
                  Chamado.aberto_por == current_user.id,
                  Chamado.tipo_chamado == 'solicitacao_administrativa',
                  Chamado.titulo.like('Pedido de acesso ao Metabase%'),
                  Chamado.status.notin_(['concluido', 'cancelado']),
              )
              .order_by(Chamado.id.desc())
              .first())
    if aberto:
        flash(f'Você já tem o chamado {aberto.numero} em aberto para este pedido.', 'warning')
        return redirect(url_for('chamados.detalhe', id=aberto.id))

    destino = _unidade_saude_digital()
    if not destino:
        flash('Não encontrei a unidade Saúde Digital para receber o chamado.', 'danger')
        return redirect(url_for('metabase.index'))

    unidade_ctx = current_user.unidade_logada or _unidade_da_pessoa()
    solicitante = unidade_ctx or destino
    cbo_unidade = cbo_na_unidade(current_user, unidade_ctx)
    tipo_unidade = ''
    if unidade_ctx and unidade_ctx.tipo_unidade:
        tipo_unidade = unidade_ctx.tipo_unidade.nome

    perfil_uso = PERFIS.get(current_user.perfil, current_user.perfil)
    perfil_cadastro = PERFIS.get(current_user.perfil_gravado, current_user.perfil_gravado)
    linha_perfil = perfil_uso
    if current_user.testando_perfil and perfil_cadastro != perfil_uso:
        linha_perfil = f'{perfil_uso} (cadastro gravado: {perfil_cadastro}; a pessoa está testando outro perfil)'

    descricao = (
        'Pedido de acesso ao Metabase feito pelo botão do SIGUS.\n'
        'Com o acesso, a pessoa abre os gráficos e confere os registros por trás dos números.\n\n'
        f'Justificativa:\n{justificativa}\n\n'
        'Dados do solicitante:\n'
        f'Nome: {current_user.nome}\n'
        f'CPF: {current_user.cpf or "—"}\n'
        f'E-mail: {current_user.email}\n'
        f'Perfil em uso no SIGUS: {linha_perfil}\n'
        f'CBO de cadastro: {rotulo_cbo(current_user.cbo)}\n'
        f'CBO na unidade: {rotulo_cbo(cbo_unidade)}\n'
        f'Unidade: {unidade_ctx.nome if unidade_ctx else "—"}\n'
        f'Tipo de unidade: {tipo_unidade or "—"}'
    )
    gravidade, urgencia, tendencia = 3, 3, 3
    chamado = Chamado(
        numero=Chamado.gerar_numero('solicitacao_administrativa'),
        unidade_id=solicitante.id,
        unidade_responsavel_id=destino.id,
        tipo_chamado='solicitacao_administrativa',
        titulo=f'Pedido de acesso ao Metabase — {current_user.nome}'[:200],
        descricao=descricao,
        prioridade=prioridade_de_gut(gravidade, urgencia, tendencia),
        sa_gravidade=gravidade,
        sa_urgencia=urgencia,
        sa_tendencia=tendencia,
        aberto_por=current_user.id,
    )
    db.session.add(chamado)
    db.session.flush()
    db.session.add(ChamadoHistorico(
        chamado_id=chamado.id,
        usuario_id=current_user.id,
        acao='Chamado de Solicitação Administrativa aberto',
        observacao='Pedido de acesso ao Metabase pelo painel do SIGUS.',
    ))
    from app.notificar import _add, _gestores_da_unidade, notificar_chamado_aberto
    notificar_chamado_aberto(chamado, current_user.id)
    if destino.id != chamado.unidade_id:
        for uid in _gestores_da_unidade(destino.id, excluir_id=current_user.id):
            _add(uid, 'chamado_aberto', f'Novo chamado: {chamado.numero}', chamado.titulo, chamado.id)
    db.session.commit()
    flash(f'Chamado {chamado.numero} aberto para a Saúde Digital.', 'success')
    return redirect(url_for('metabase.index'))


@metabase_bp.route('/configurar')
@login_required
def cfg():
    if not _pode_gerir():
        abort(403)
    itens = MetabasePainel.query.order_by(MetabasePainel.ordem, MetabasePainel.id).all()
    return render_template(
        'metabase/admin.html',
        config=_config(),
        itens=itens,
        perfis=PERFIS_LINK,
        tipos_unidade={t.id: t for t in TipoUnidade.query.order_by(TipoUnidade.nome).all()},
    )


@metabase_bp.route('/configurar/conexao', methods=['POST'])
@login_required
def cfg_conexao():
    if not current_user.pode('editar_metabase') and not current_user.pode('adicionar_metabase'):
        abort(403)
    cfg = _config()
    site = (request.form.get('site_url') or '').strip().rstrip('/')
    if not (site.startswith('http://') or site.startswith('https://')):
        flash('Informe a URL do Metabase começando com http:// ou https://.', 'danger')
        return redirect(url_for('metabase.cfg'))
    try:
        intervalo = int(request.form.get('intervalo_segundos') or 40)
    except (TypeError, ValueError):
        intervalo = 0
    if intervalo < _INTERVALO_MIN or intervalo > _INTERVALO_MAX:
        flash(f'O tempo da apresentação fica entre {_INTERVALO_MIN} e {_INTERVALO_MAX} segundos.', 'danger')
        return redirect(url_for('metabase.cfg'))
    chave = (request.form.get('secret_key') or '').strip()
    if chave:
        cfg.secret_key = chave
    elif not cfg.chave_gravada:
        flash('Informe a chave secreta de incorporação do Metabase.', 'danger')
        return redirect(url_for('metabase.cfg'))
    cfg.site_url = site
    cfg.intervalo_segundos = intervalo
    db.session.commit()
    flash('Conexão do Metabase salva.', 'success')
    return redirect(url_for('metabase.cfg'))


@metabase_bp.route('/configurar/novo', methods=['GET', 'POST'])
@login_required
def cfg_novo():
    if not _pode_gerir():
        abort(403)
    if request.method == 'POST':
        dados, erro = _ler_painel(None)
        if erro:
            flash(erro, 'danger')
            return render_template('metabase/form.html', item=None, **_opcoes_form())
        ultimo = MetabasePainel.query.order_by(MetabasePainel.ordem.desc()).first()
        item = MetabasePainel(
            **dados,
            ordem=(ultimo.ordem + 1 if ultimo else 0),
            criado_por=current_user.id,
        )
        db.session.add(item)
        db.session.commit()
        flash(f'"{item.nome}" adicionado.', 'success')
        return redirect(url_for('metabase.cfg'))
    return render_template('metabase/form.html', item=None, **_opcoes_form())


@metabase_bp.route('/configurar/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def cfg_editar(id):
    if not _pode_gerir():
        abort(403)
    item = MetabasePainel.query.get_or_404(id)
    if request.method == 'POST':
        dados, erro = _ler_painel(item)
        if erro:
            flash(erro, 'danger')
            return render_template('metabase/form.html', item=item, **_opcoes_form())
        for chave, valor in dados.items():
            setattr(item, chave, valor)
        db.session.commit()
        flash(f'"{item.nome}" atualizado.', 'success')
        return redirect(url_for('metabase.cfg'))
    return render_template('metabase/form.html', item=item, **_opcoes_form())


@metabase_bp.route('/configurar/<int:id>/excluir', methods=['POST'])
@login_required
def cfg_excluir(id):
    if not _pode_gerir():
        abort(403)
    item = MetabasePainel.query.get_or_404(id)
    nome = item.nome
    db.session.delete(item)
    db.session.commit()
    flash(f'"{nome}" excluído.', 'success')
    return redirect(url_for('metabase.cfg'))


@metabase_bp.route('/configurar/reordenar', methods=['POST'])
@login_required
def cfg_reordenar():
    if not _pode_gerir():
        abort(403)
    ids = (request.get_json(silent=True) or {}).get('ids') or []
    for ordem, item_id in enumerate(ids):
        MetabasePainel.query.filter_by(id=item_id).update({'ordem': ordem})
    db.session.commit()
    return jsonify({'ok': True})
