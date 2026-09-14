# -*- coding: utf-8 -*-
"""Comunicados com ciência e mural de ações da rede."""
import os
import uuid
import mimetypes
from datetime import date, datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
)
from flask_login import login_required, current_user
from sqlalchemy import extract
from sqlalchemy.orm import joinedload, selectinload
from app import db
from app.utils import agora_local
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.usuario import Usuario
from app.models.notificacao import Notificacao
from app.models.noticias import (
    TipoAcao, Comunicado, ComunicadoAnexo, ComunicadoCiencia,
    AcaoLocal, AcaoLocalFoto,
    DESCRICAO_ACAO_MAX, FOTOS_ACAO_MAX, ANEXOS_COMUNICADO_MAX,
    PERFIS_PUBLICAR, PERFIS_COMPARTILHAR,
)
from app.models.transferencia import ItemLojinha

noticias_bp = Blueprint('noticias', __name__)

_DIR_COMUNICADOS = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'comunicados'
)
_DIR_ACOES = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'acoes'
)

_ANEXO_EXTS = {'.pdf', '.doc', '.docx', '.odt', '.jpg', '.jpeg', '.png', '.webp'}
_FOTO_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
_ANEXO_MAX_MB = 10
_FOTO_MAX_MB = 5
_ASSINATURA_PREFIXO = 'data:image/png;base64,'
_ASSINATURA_MAX = 400_000
_ASSINATURA_MIN = 8_000


def _ip_cliente():
    for h in ('X-Forwarded-For', 'X-Real-IP'):
        v = (request.headers.get(h) or '').split(',')[0].strip()
        if v:
            return v[:45]
    return (request.remote_addr or '')[:45]


def _user_agent():
    return (request.headers.get('User-Agent') or '')[:400]


def _assinatura_form():
    raw = (request.form.get('assinatura_base64') or '').strip()
    if not raw.startswith(_ASSINATURA_PREFIXO):
        return None
    if len(raw) < _ASSINATURA_MIN or len(raw) > _ASSINATURA_MAX:
        return None
    return raw


def _cpf_digitos(valor):
    return ''.join(c for c in (valor or '') if c.isdigit())[:11]


def _cpf_form():
    d = _cpf_digitos(request.form.get('cpf'))
    return d if len(d) == 11 else None


def _registrar_ciencia(item, origem, exigir_assinatura=False):
    """Cria o registro de ciência com trilha de auditoria."""
    assinatura = _assinatura_form()
    if exigir_assinatura and not assinatura:
        return None, 'Assine no campo abaixo para registrar a ciência.'
    cpf_cadastro = _cpf_digitos(getattr(current_user, 'cpf', None))
    cpf_informado = _cpf_form()
    if exigir_assinatura:
        if len(cpf_cadastro) != 11:
            return None, 'Seu cadastro no SIGUS está sem CPF. Atualize o perfil antes de dar ciência.'
        if not cpf_informado:
            return None, 'Informe o CPF para confirmar a identidade.'
        if cpf_informado != cpf_cadastro:
            return None, 'O CPF não confere com o cadastro. Confira os números.'
    un = current_user.unidade_logada
    rec = ComunicadoCiencia(
        comunicado_id=item.id,
        usuario_id=current_user.id,
        ciencia_em=agora_local(),
        ip=_ip_cliente() or None,
        user_agent=_user_agent() or None,
        unidade_id=un.id if un else None,
        assinatura_base64=assinatura,
        origem=origem,
        cpf=cpf_informado or (cpf_cadastro if len(cpf_cadastro) == 11 else None),
    )
    db.session.add(rec)
    return rec, None


def pode_publicar(usuario=None):
    u = usuario or current_user
    return bool(u.is_authenticated and u.perfil in PERFIS_PUBLICAR)


def pode_compartilhar(usuario=None):
    u = usuario or current_user
    return bool(u.is_authenticated and u.perfil in PERFIS_COMPARTILHAR)


def _exigir_publicar():
    if not pode_publicar():
        abort(403)


def unidades_ativas():
    return Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()


def unidades_para_publicar():
    """Unidades que o usuário pode escolher ao publicar."""
    if current_user.perfil in ('administrador', 'gestor_secretaria'):
        return unidades_ativas()
    u = current_user.unidade_logada
    return [u] if u else []


def _ids_form_unidades():
    raw = request.form.getlist('unidades')
    ids = []
    for v in raw:
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue
    return ids


def resolver_unidades_comunicado():
    """Valida unidades alvo de um comunicado conforme o perfil."""
    permitidas = {u.id for u in unidades_para_publicar()}
    if not permitidas:
        return None, 'Selecione uma unidade no topo para publicar.'

    if not pode_compartilhar():
        u = current_user.unidade_logada
        if not u:
            return None, 'Selecione uma unidade no topo para publicar.'
        return [u], None

    escolhidas = _ids_form_unidades()
    if not escolhidas and current_user.unidade_logada:
        escolhidas = [current_user.unidade_logada.id]
    escolhidas = [i for i in escolhidas if i in permitidas]
    if not escolhidas:
        return None, 'Escolha ao menos uma unidade para o comunicado.'
    unidades = Unidade.query.filter(Unidade.id.in_(escolhidas), Unidade.status == 'ativa').all()
    if not unidades:
        return None, 'Nenhuma unidade válida selecionada.'
    return unidades, None


def resolver_unidade_acao():
    permitidas = {u.id for u in unidades_para_publicar()}
    if not permitidas:
        return None, 'Selecione uma unidade no topo para registrar a ação.'
    if current_user.perfil in ('administrador', 'gestor_secretaria'):
        try:
            uid = int(request.form.get('unidade_id') or 0)
        except (TypeError, ValueError):
            uid = 0
        if not uid and current_user.unidade_logada:
            uid = current_user.unidade_logada.id
        if uid not in permitidas:
            return None, 'Escolha a unidade onde a ação aconteceu.'
        un = Unidade.query.filter_by(id=uid, status='ativa').first()
        if not un:
            return None, 'Unidade inválida.'
        return un, None
    un = current_user.unidade_logada
    if not un:
        return None, 'Selecione uma unidade no topo para registrar a ação.'
    return un, None


def ids_destinatarios(comunicado):
    unidade_ids = comunicado.ids_unidades_alvo()
    if not unidade_ids:
        return set()
    rows = (
        db.session.query(UsuarioUnidade.usuario_id)
        .join(Usuario, Usuario.id == UsuarioUnidade.usuario_id)
        .filter(
            UsuarioUnidade.unidade_id.in_(unidade_ids),
            UsuarioUnidade.ativo.is_(True),
            Usuario.ativo.is_(True),
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows} | ({comunicado.autor_id} if comunicado.autor_id else set())


def usuarios_destinatarios(comunicado):
    ids = ids_destinatarios(comunicado)
    if not ids:
        return []
    return (
        Usuario.query
        .filter(Usuario.id.in_(ids))
        .order_by(Usuario.nome)
        .all()
    )


def usuario_deve_ciencia(comunicado, usuario_id):
    if not comunicado.exige_ciencia or not comunicado.ativo:
        return False
    return usuario_id in ids_destinatarios(comunicado)


def _salvar_arquivo(file_obj, pasta, exts, max_mb):
    original = (file_obj.filename or '').strip()
    if not original:
        return None, 'Arquivo sem nome.'
    ext = os.path.splitext(original)[1].lower()
    if ext not in exts:
        return None, f'Tipo não permitido: {original}'
    data = file_obj.read()
    if not data:
        return None, f'Arquivo vazio: {original}'
    if len(data) > max_mb * 1024 * 1024:
        return None, f'{original} passa de {max_mb} MB.'
    os.makedirs(pasta, exist_ok=True)
    filename = f'{uuid.uuid4().hex}{ext}'
    with open(os.path.join(pasta, filename), 'wb') as fh:
        fh.write(data)
    mime = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    return {
        'filename': filename,
        'original': original[:255],
        'mime_type': mime[:80],
        'tamanho_bytes': len(data),
    }, None


def _notificar_comunicado(comunicado):
    destinos = ids_destinatarios(comunicado)
    destinos.discard(comunicado.autor_id)
    for uid in destinos:
        db.session.add(Notificacao(
            usuario_id=uid,
            tipo='comunicado_novo',
            titulo=comunicado.titulo,
            texto='Novo comunicado na sua unidade. Dê ciência.',
            comunicado_id=comunicado.id,
        ))


def comunicados_da_unidade(unidade_id, limite=12):
    """Comunicados ativos que incluem a unidade alvo."""
    if not unidade_id:
        return []
    return (
        Comunicado.query
        .options(selectinload(Comunicado.anexos), selectinload(Comunicado.autor))
        .filter(
            Comunicado.ativo.is_(True),
            Comunicado.unidades_alvo.any(Unidade.id == unidade_id),
        )
        .order_by(Comunicado.criado_em.desc())
        .limit(limite)
        .all()
    )


def montar_cards_comunicados(comunicados, usuario_id):
    cards = []
    for c in comunicados:
        dest = ids_destinatarios(c)
        n_dest = len(dest)
        n_ok = c.ciencias.count() if c.exige_ciencia else 0
        deve = c.exige_ciencia and usuario_id in dest
        ja = c.usuario_cientificou(usuario_id) if deve else False
        cards.append({
            'item': c,
            'n_dest': n_dest,
            'n_ok': n_ok,
            'pendente': deve and not ja,
            'ja_ciencia': ja,
            'deve_ciencia': deve,
        })
    cards.sort(key=lambda x: (not x['pendente'], -(x['item'].criado_em.timestamp() if x['item'].criado_em else 0)))
    return cards


def acoes_recentes(limite=8, unidade_id=None, tipo_id=None, ano=None, mes=None):
    q = AcaoLocal.query.options(
        selectinload(AcaoLocal.fotos),
        joinedload(AcaoLocal.unidade),
        joinedload(AcaoLocal.tipo),
        joinedload(AcaoLocal.autor),
    )
    if unidade_id:
        q = q.filter(AcaoLocal.unidade_id == unidade_id)
    if tipo_id:
        q = q.filter(AcaoLocal.tipo_acao_id == tipo_id)
    if ano and mes:
        q = q.filter(
            extract('year', AcaoLocal.data_acao) == ano,
            extract('month', AcaoLocal.data_acao) == mes,
        )
    return q.order_by(AcaoLocal.data_acao.desc(), AcaoLocal.criado_em.desc()).limit(limite).all()


def _itens_lojinha_mural(limite=20, unidade_id=None, ano=None, mes=None):
    q = ItemLojinha.query.options(
        joinedload(ItemLojinha.unidade),
        joinedload(ItemLojinha.destino_unidade),
        joinedload(ItemLojinha.criador),
        joinedload(ItemLojinha.equipamento),
    )
    if unidade_id:
        q = q.filter(ItemLojinha.unidade_id == unidade_id)
    if ano and mes:
        q = q.filter(
            extract('year', ItemLojinha.criado_em) == ano,
            extract('month', ItemLojinha.criado_em) == mes,
        )
    return q.order_by(ItemLojinha.criado_em.desc()).limit(limite).all()


def feed_mural(limite=20, unidade_id=None, tipo_id=None, ano=None, mes=None, so_lojinha=False):
    """Feed misto: ações da rede + itens da lojinha, do mais novo para o mais antigo."""
    itens = []
    acoes = []
    if not so_lojinha:
        acoes = acoes_recentes(
            limite=limite, unidade_id=unidade_id, tipo_id=tipo_id, ano=ano, mes=mes,
        )
    if not tipo_id:
        itens = _itens_lojinha_mural(limite=limite, unidade_id=unidade_id, ano=ano, mes=mes)
    feed = []
    for a in acoes:
        quando = a.criado_em or datetime.combine(a.data_acao, datetime.min.time())
        feed.append({'tipo': 'acao', 'quando': quando, 'acao': a})
    for i in itens:
        feed.append({'tipo': 'lojinha', 'quando': i.criado_em, 'item': i})
    feed.sort(key=lambda x: x['quando'] or datetime.min, reverse=True)
    return feed[:limite]


def _ctx_acao(tipos, unidades, escolher_unidade):
    return dict(
        tipos=tipos,
        unidades=unidades,
        escolher_unidade=escolher_unidade,
        max_desc=DESCRICAO_ACAO_MAX,
        hoje_iso=date.today().isoformat(),
    )


def _ctx_comunicado(unidades):
    marcadas = request.form.getlist('unidades')
    if not marcadas and current_user.unidade_logada:
        marcadas = [str(current_user.unidade_logada.id)]
    return dict(
        unidades=unidades,
        pode_compartilhar=pode_compartilhar(),
        marcadas=marcadas,
    )


@noticias_bp.route('/comunicados/novo', methods=['GET', 'POST'])
@login_required
def novo_comunicado():
    _exigir_publicar()
    unidades = unidades_para_publicar()
    ctx = _ctx_comunicado(unidades)
    if request.method == 'POST':
        titulo = (request.form.get('titulo') or '').strip()
        texto = (request.form.get('texto') or '').strip()
        if not titulo:
            flash('Informe o título do comunicado.', 'danger')
            return render_template('noticias/comunicado_form.html', **ctx)
        alvos, erro = resolver_unidades_comunicado()
        if erro:
            flash(erro, 'danger')
            return render_template('noticias/comunicado_form.html', **ctx)
        arquivos = request.files.getlist('anexos')
        arquivos = [f for f in arquivos if f and f.filename]
        if len(arquivos) > ANEXOS_COMUNICADO_MAX:
            flash(f'No máximo {ANEXOS_COMUNICADO_MAX} anexos.', 'danger')
            return render_template('noticias/comunicado_form.html', **ctx)
        salvos = []
        for f in arquivos:
            meta, err = _salvar_arquivo(f, _DIR_COMUNICADOS, _ANEXO_EXTS, _ANEXO_MAX_MB)
            if err:
                flash(err, 'danger')
                return render_template('noticias/comunicado_form.html', **ctx)
            salvos.append(meta)

        origem = current_user.unidade_logada or alvos[0]
        comunicado = Comunicado(
            titulo=titulo[:200],
            texto=texto or None,
            autor_id=current_user.id,
            unidade_origem_id=origem.id if origem else None,
            exige_ciencia=request.form.get('exige_ciencia') == 'on',
        )
        comunicado.unidades_alvo = alvos
        db.session.add(comunicado)
        db.session.flush()
        for meta in salvos:
            db.session.add(ComunicadoAnexo(comunicado_id=comunicado.id, **meta))
        _notificar_comunicado(comunicado)
        db.session.commit()
        if comunicado.exige_ciencia:
            flash('Comunicado publicado. Assine para registrar a sua ciência.', 'success')
            return redirect(url_for('noticias.detalhe_comunicado', id=comunicado.id) + '#ciencia')
        flash('Comunicado publicado.', 'success')
        return redirect(url_for('noticias.detalhe_comunicado', id=comunicado.id))

    return render_template('noticias/comunicado_form.html', **ctx)


@noticias_bp.route('/comunicados/<int:id>')
@login_required
def detalhe_comunicado(id):
    item = Comunicado.query.get_or_404(id)
    if not item.ativo:
        abort(404)
    dest = usuarios_destinatarios(item)
    dest_ids = {u.id for u in dest}
    if not (pode_publicar() or current_user.id in dest_ids or item.autor_id == current_user.id):
        abort(403)
    ciencias = {c.usuario_id: c for c in item.ciencias.all()}
    deve = item.exige_ciencia and current_user.id in dest_ids
    ja = current_user.id in ciencias
    ver_lista = pode_publicar() or item.autor_id == current_user.id
    faltam = [u for u in dest if u.id not in ciencias] if ver_lista else []
    deram = [ciencias[u.id] for u in dest if u.id in ciencias] if ver_lista else []
    deram.sort(key=lambda c: c.ciencia_em or datetime.min)
    minha = ciencias.get(current_user.id)
    return render_template(
        'noticias/comunicado_detalhe.html',
        item=item,
        deve_ciencia=deve,
        ja_ciencia=ja,
        n_dest=len(dest),
        n_ok=len(ciencias),
        ver_lista=ver_lista,
        faltam=faltam,
        deram=deram,
        minha_ciencia=minha,
    )


@noticias_bp.route('/comunicados/<int:id>/ciencia', methods=['POST'])
@login_required
def dar_ciencia(id):
    item = Comunicado.query.get_or_404(id)
    if not item.ativo or not item.exige_ciencia:
        abort(404)
    if not usuario_deve_ciencia(item, current_user.id):
        flash('Este comunicado não pede a sua ciência.', 'warning')
        return redirect(url_for('noticias.detalhe_comunicado', id=item.id))
    if item.usuario_cientificou(current_user.id):
        flash('Você já deu ciência neste comunicado.', 'info')
        return redirect(url_for('noticias.detalhe_comunicado', id=item.id))
    rec, erro = _registrar_ciencia(item, 'formulario', exigir_assinatura=True)
    if erro:
        flash(erro, 'danger')
        return redirect(url_for('noticias.detalhe_comunicado', id=item.id) + '#ciencia')
    db.session.commit()
    flash('Ciência registrada.', 'success')
    return redirect(url_for('noticias.detalhe_comunicado', id=item.id))


@noticias_bp.route('/comunicados/<int:id>/imprimir')
@login_required
def imprimir_comunicado(id):
    item = Comunicado.query.get_or_404(id)
    if not item.ativo:
        abort(404)
    dest = usuarios_destinatarios(item)
    dest_ids = {u.id for u in dest}
    if not (pode_publicar() or current_user.id in dest_ids or item.autor_id == current_user.id):
        abort(403)
    ciencias = {c.usuario_id: c for c in item.ciencias.all()}
    deram = [ciencias[u.id] for u in dest if u.id in ciencias]
    for uid, rec in ciencias.items():
        if uid not in dest_ids:
            deram.append(rec)
    deram.sort(key=lambda c: c.ciencia_em or datetime.min)
    faltam = [u for u in dest if u.id not in ciencias]
    return render_template(
        'noticias/comunicado_imprimir.html',
        item=item,
        deram=deram,
        faltam=faltam,
        n_dest=len(dest),
        n_ok=len(ciencias),
        agora=agora_local(),
    )


@noticias_bp.route('/acoes/nova', methods=['GET', 'POST'])
@login_required
def nova_acao():
    _exigir_publicar()
    tipos = TipoAcao.query.filter_by(ativo=True).order_by(TipoAcao.ordem, TipoAcao.nome).all()
    unidades = unidades_para_publicar()
    escolher_unidade = current_user.perfil in ('administrador', 'gestor_secretaria')
    ctx = _ctx_acao(tipos, unidades, escolher_unidade)
    if request.method == 'POST':
        descricao = (request.form.get('descricao') or '').strip()
        if not descricao:
            flash('Escreva uma descrição breve da ação.', 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        if len(descricao) > DESCRICAO_ACAO_MAX:
            flash(f'A descrição pode ter no máximo {DESCRICAO_ACAO_MAX} caracteres.', 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        try:
            tipo_id = int(request.form.get('tipo_acao_id') or 0)
        except (TypeError, ValueError):
            tipo_id = 0
        tipo = TipoAcao.query.filter_by(id=tipo_id, ativo=True).first()
        if not tipo:
            flash('Escolha o tema da ação.', 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        data_raw = (request.form.get('data_acao') or '').strip()
        try:
            data_acao = datetime.strptime(data_raw, '%Y-%m-%d').date() if data_raw else date.today()
        except ValueError:
            data_acao = date.today()
        un, erro = resolver_unidade_acao()
        if erro:
            flash(erro, 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        arquivos = [f for f in request.files.getlist('fotos') if f and f.filename]
        if not arquivos:
            flash('Envie ao menos uma foto da ação.', 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        if len(arquivos) > FOTOS_ACAO_MAX:
            flash(f'No máximo {FOTOS_ACAO_MAX} fotos.', 'danger')
            return render_template('noticias/acao_form.html', **ctx)
        salvos = []
        for f in arquivos:
            meta, err = _salvar_arquivo(f, _DIR_ACOES, _FOTO_EXTS, _FOTO_MAX_MB)
            if err:
                flash(err, 'danger')
                return render_template('noticias/acao_form.html', **ctx)
            salvos.append(meta)

        acao = AcaoLocal(
            unidade_id=un.id,
            autor_id=current_user.id,
            tipo_acao_id=tipo.id,
            descricao=descricao,
            data_acao=data_acao,
        )
        db.session.add(acao)
        db.session.flush()
        for i, meta in enumerate(salvos):
            db.session.add(AcaoLocalFoto(
                acao_id=acao.id,
                filename=meta['filename'],
                original=meta['original'],
                mime_type=meta['mime_type'],
                ordem=i,
            ))
        db.session.commit()
        flash('Ação publicada no mural da rede.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('noticias/acao_form.html', **ctx)


@noticias_bp.route('/mural')
@login_required
def mural():
    tipos = TipoAcao.query.filter_by(ativo=True).order_by(TipoAcao.ordem, TipoAcao.nome).all()
    unidades = unidades_ativas()
    try:
        unidade_id = int(request.args.get('unidade') or 0) or None
    except (TypeError, ValueError):
        unidade_id = None
    try:
        tipo_id = int(request.args.get('tipo') or 0) or None
    except (TypeError, ValueError):
        tipo_id = None
    mes_raw = (request.args.get('mes') or '').strip()
    ano = mes = None
    if mes_raw:
        try:
            dt = datetime.strptime(mes_raw, '%Y-%m')
            ano, mes = dt.year, dt.month
        except ValueError:
            mes_raw = ''
    so_lojinha = (request.args.get('tipo') or '') == 'lojinha'
    tipo_id = None if so_lojinha else tipo_id
    feed = feed_mural(
        limite=60,
        unidade_id=unidade_id,
        tipo_id=tipo_id,
        ano=ano,
        mes=mes,
        so_lojinha=so_lojinha,
    )
    return render_template(
        'noticias/mural.html',
        feed=feed,
        tipos=tipos,
        unidades=unidades,
        filtro_unidade=unidade_id,
        filtro_tipo='lojinha' if so_lojinha else tipo_id,
        filtro_mes=mes_raw,
        pode_publicar=pode_publicar(),
    )
