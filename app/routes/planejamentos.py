# -*- coding: utf-8 -*-
"""Planejamentos/Projetos com Kanban e GUT — estilo Monday.com."""
import os
import uuid
import mimetypes
from datetime import datetime, timedelta, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.planejamento import (
    Planejamento, AcaoPlanejamento, AcaoObservacao, AcaoObservacaoAnexo,
    PlanejamentoAnexo, STATUS_ACAO, STATUS_ACAO_LABELS,
)

planejamentos_bp = Blueprint('planejamentos', __name__, url_prefix='/planejamentos')

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'planos')
_UPLOAD_DIR_OBS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'obs_acoes')
_MAX_MB = 20
_ALLOWED = ('image/', 'application/pdf')


def _salvar_anexo(file_obj, planejamento_id):
    """Salva PDF ou imagem e retorna PlanejamentoAnexo."""
    original = file_obj.filename or 'sem_nome'
    mime = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    if not any(mime.startswith(p) for p in _ALLOWED):
        return None
    ext = os.path.splitext(original)[1].lower() or '.bin'
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    file_obj.save(os.path.join(_UPLOAD_DIR, filename))
    return PlanejamentoAnexo(planejamento_id=planejamento_id, filename=filename, original=original, mime_type=mime)


def _links_nova_aba(html):
    """Garante que links no HTML abram em nova aba."""
    if not html or '<a ' not in html:
        return html
    import re
    return re.sub(r'<a\s+([^>]*?)>', r'<a \1 target="_blank" rel="noopener">', html)


def _salvar_obs_anexo(file_obj, observacao_id):
    """Salva PDF ou imagem em observação e retorna AcaoObservacaoAnexo."""
    original = file_obj.filename or 'sem_nome'
    mime = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    if not any(mime.startswith(p) for p in _ALLOWED):
        return None
    ext = os.path.splitext(original)[1].lower() or '.bin'
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(_UPLOAD_DIR_OBS, exist_ok=True)
    file_obj.save(os.path.join(_UPLOAD_DIR_OBS, filename))
    return AcaoObservacaoAnexo(
        observacao_id=observacao_id, filename=filename, original=original, mime_type=mime
    )


def _ids_unidades_usuario():
    """IDs das unidades que o usuário pode ver (suas vinculadas)."""
    if current_user.pode('ver_todas_unidades'):
        from app.models.unidade import Unidade
        return [u.id for u in Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()]
    return [u.id for u in current_user.unidades_ativas]


def _usuarios_unidade(unidade_id):
    """Usuários vinculados à unidade (para atribuir responsáveis)."""
    from app.models.unidade import UsuarioUnidade
    vincs = UsuarioUnidade.query.filter_by(unidade_id=unidade_id, ativo=True).all()
    usuarios = [v.usuario for v in vincs if v.usuario]
    return sorted(usuarios, key=lambda u: (u.nome or '').lower())


def _resp_display_html(acao):
    """Retorna HTML do bloco de responsáveis/empresas para atualização via AJAX."""
    parts = []
    for r in acao.responsaveis:
        nome = (r.nome or '').split()
        primeiro = nome[0] if nome else '?'
        foto = f'<img src="{r.foto_url}" alt="" class="resp-avatar">' if getattr(r, 'foto_url', None) and r.foto_url else f'<span class="resp-inicial">{getattr(r, "inicial", primeiro[0].upper())}</span>'
        parts.append(f'<div class="resp-item" title="{r.nome or ""}">{foto}<span class="resp-nome">{primeiro}</span></div>')
    for e in acao.empresas:
        nome = (e.nome_comum or e.razao_social or '')[:20]
        if len(e.nome_comum or e.razao_social or '') > 20:
            nome += '…'
        foto = f'<img src="{e.foto_url}" alt="" class="resp-avatar">' if e.foto_url else '<span class="resp-inicial resp-empresa"><i class="bi bi-building"></i></span>'
        parts.append(f'<div class="resp-item" title="{e.razao_social or ""}">{foto}<span class="resp-nome">{nome}</span></div>')
    if not parts:
        return '<span class="text-muted">—</span>'
    return '<div class="d-flex flex-wrap align-items-center gap-1">' + ''.join(parts) + '</div>'


@planejamentos_bp.route('/')
@login_required
def listar():
    from app.models.unidade import Unidade
    from app.models.planejamento import acacao_planejamento_responsaveis, STATUS_ACAO_LABELS

    ids = _ids_unidades_usuario()
    if not ids:
        flash('Você precisa estar vinculado a pelo menos uma unidade para acessar os planejamentos.', 'warning')
        return redirect(url_for('dashboard.index'))

    unidade_id = request.args.get('unidade_id', type=int)
    aba = request.args.get('aba', 'abertos')  # abertos | concluidos | cancelados
    if aba not in ('abertos', 'concluidos', 'cancelados'):
        aba = 'abertos'
    expand_id = None
    if unidade_id and unidade_id not in ids:
        unidade_id = None
    if unidade_id is None and len(ids) == 1:
        unidade_id = ids[0]

    unidades = Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()

    q = Planejamento.query.filter(Planejamento.unidade_id.in_(ids))
    if unidade_id:
        q = q.filter(Planejamento.unidade_id == unidade_id)
    q = q.order_by(
        db.desc(Planejamento.gravidade * Planejamento.urgencia * Planejamento.tendencia),
        Planejamento.titulo,
    )
    planejamentos_todos = q.all()

    def _status_plano(p):
        acoes = list(p.acoes.all())
        total = len(acoes)
        if total == 0:
            return 'abertos'
        concluidas = sum(1 for a in acoes if a.status == 'concluido')
        canceladas = sum(1 for a in acoes if a.status == 'cancelado')
        em_andamento = sum(1 for a in acoes if a.status == 'em_andamento')
        pendentes = sum(1 for a in acoes if a.status == 'backlog')
        if canceladas == total:
            return 'cancelados'
        if em_andamento or pendentes:
            return 'abertos'
        if concluidas > 0:
            return 'concluidos'
        return 'abertos'

    contagem_por_aba = {'abertos': 0, 'concluidos': 0, 'cancelados': 0}
    for p in planejamentos_todos:
        st = _status_plano(p)
        contagem_por_aba[st] = contagem_por_aba.get(st, 0) + 1

    planejamentos = [p for p in planejamentos_todos if _status_plano(p) == aba]

    # Para cada planejamento: acoes, progresso, usuarios
    planejamentos_dados = []
    planej_ids = [p.id for p in planejamentos]
    contagem_acoes_usuario = {}
    ids_com_minhas_acoes = set()

    if planej_ids:
        rows = db.session.query(
            AcaoPlanejamento.planejamento_id,
            db.func.count(AcaoPlanejamento.id).label('cnt')
        ).join(
            acacao_planejamento_responsaveis,
            db.and_(
                acacao_planejamento_responsaveis.c.acao_id == AcaoPlanejamento.id,
                acacao_planejamento_responsaveis.c.usuario_id == current_user.id
            )
        ).filter(
            AcaoPlanejamento.planejamento_id.in_(planej_ids),
            AcaoPlanejamento.status.notin_(['concluido', 'cancelado'])
        ).group_by(AcaoPlanejamento.planejamento_id).all()
        for pid, cnt in rows:
            contagem_acoes_usuario[pid] = cnt
            ids_com_minhas_acoes.add(pid)

    hoje = date.today()
    for p in planejamentos:
        acoes_flat = list(p.acoes.order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id))
        total = len(acoes_flat)
        concluidas = sum(1 for a in acoes_flat if a.status == 'concluido')
        canceladas = sum(1 for a in acoes_flat if a.status == 'cancelado')
        em_andamento = sum(1 for a in acoes_flat if a.status == 'em_andamento')
        pendentes = sum(1 for a in acoes_flat if a.status == 'backlog')
        atrasadas = sum(1 for a in acoes_flat if a.status not in ('concluido', 'cancelado') and a.prazo and a.prazo < hoje)
        total_ativas = total - canceladas
        progresso_pct = round(100 * concluidas / total_ativas) if total_ativas else 0
        em_andamento_pct = round(100 * em_andamento / total_ativas) if total_ativas else 0
        pendentes_pct = round(100 * pendentes / total_ativas) if total_ativas else 0
        usuarios = _usuarios_unidade(p.unidade_id)
        from app.models.empresa import EmpresaContratada
        empresas = EmpresaContratada.query.filter_by(ativo=True).order_by(EmpresaContratada.razao_social).all()
        planejamentos_dados.append({
            'plano': p,
            'acoes_flat': acoes_flat,
            'progresso_pct': progresso_pct,
            'em_andamento_pct': em_andamento_pct,
            'pendentes_pct': pendentes_pct,
            'usuarios': usuarios,
            'empresas': empresas,
            'status_resumo': {'atrasadas': atrasadas, 'pendentes': pendentes, 'em_andamento': em_andamento, 'concluidas': concluidas, 'canceladas': canceladas},
        })

    tem_planos_geral = len(planejamentos_todos) > 0
    return render_template(
        'planejamentos/listar.html',
        planejamentos_dados=planejamentos_dados,
        unidades=unidades,
        unidade_id=unidade_id,
        aba=aba,
        contagem_por_aba=contagem_por_aba,
        tem_planos_geral=tem_planos_geral,
        expand_id=expand_id,
        status_opts=STATUS_ACAO_LABELS,
        pode_criar=current_user.pode('criar_plano'),
        pode_criar_acao=current_user.pode('criar_acao'),
        pode_editar_gut=current_user.pode('editar_plano_gut'),
        pode_alterar_status=current_user.pode('alterar_status_acao'),
        contagem_acoes_usuario=contagem_acoes_usuario,
        ids_com_minhas_acoes=ids_com_minhas_acoes,
    )


@planejamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def criar():
    if not current_user.pode('criar_plano'):
        abort(403)

    ids = _ids_unidades_usuario()
    if not ids:
        flash('Vincule-se a uma unidade para criar planejamentos.', 'warning')
        return redirect(url_for('planejamentos.listar'))

    from app.models.unidade import Unidade
    unidades = Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        unidade_id = request.form.get('unidade_id', type=int)
        g = request.form.get('gravidade', 1, type=int)
        u = request.form.get('urgencia', 1, type=int)
        t = request.form.get('tendencia', 1, type=int)

        if not titulo:
            flash('Título é obrigatório.', 'danger')
            return redirect(url_for('planejamentos.criar'))

        if unidade_id not in ids:
            abort(403)

        g = max(1, min(5, g))
        u = max(1, min(5, u))
        t = max(1, min(5, t))

        now = datetime.utcnow()
        planejamento = Planejamento(
            unidade_id=unidade_id,
            titulo=titulo,
            descricao=descricao or None,
            gravidade=g, urgencia=u, tendencia=t,
            criado_por=current_user.id,
            atualizado_em=now,
            atualizado_por=current_user.id,
        )
        db.session.add(planejamento)
        db.session.flush()

        for f in request.files.getlist('anexos')[:15]:
            if f and f.filename:
                conteudo = f.read()
                f.seek(0)
                if len(conteudo) / (1024 * 1024) <= _MAX_MB:
                    anexo = _salvar_anexo(f, planejamento.id)
                    if anexo:
                        db.session.add(anexo)

        db.session.commit()
        flash('Planejamento criado com sucesso.', 'success')
        return redirect(url_for('planejamentos.listar', expand=planejamento.id, unidade_id=planejamento.unidade_id))

    return render_template('planejamentos/form_planejamento.html', unidades=unidades, planejamento=None)


@planejamentos_bp.route('/<int:id>')
@planejamentos_bp.route('/<int:id>/kanban')
@login_required
def projeto_detalhe(id):
    """Redireciona para listar com o projeto expandido."""
    planejamento = Planejamento.query.get_or_404(id)
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)
    return redirect(url_for('planejamentos.listar', expand=id, unidade_id=planejamento.unidade_id))


@planejamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_plano_gut'):
        abort(403)

    planejamento = Planejamento.query.get_or_404(id)
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        g = request.form.get('gravidade', 1, type=int)
        u = request.form.get('urgencia', 1, type=int)
        t = request.form.get('tendencia', 1, type=int)

        if not titulo:
            flash('Título é obrigatório.', 'danger')
            return redirect(url_for('planejamentos.editar', id=id))

        planejamento.titulo = titulo
        planejamento.descricao = descricao or None
        planejamento.gravidade = max(1, min(5, g))
        planejamento.urgencia = max(1, min(5, u))
        planejamento.tendencia = max(1, min(5, t))
        planejamento.atualizado_em = datetime.utcnow()
        planejamento.atualizado_por = current_user.id

        for f in request.files.getlist('anexos')[:15]:
            if f and f.filename:
                conteudo = f.read()
                f.seek(0)
                if len(conteudo) / (1024 * 1024) <= _MAX_MB:
                    anexo = _salvar_anexo(f, planejamento.id)
                    if anexo:
                        db.session.add(anexo)

        db.session.commit()
        flash('Planejamento atualizado.', 'success')
        return redirect(url_for('planejamentos.listar', expand=planejamento.id, unidade_id=planejamento.unidade_id))

    return render_template('planejamentos/form_planejamento.html', planejamento=planejamento, unidades=[planejamento.unidade])


@planejamentos_bp.route('/<int:plano_id>/acoes/nova', methods=['POST'])
@login_required
def criar_acao(plano_id):
    if not current_user.pode('criar_acao'):
        abort(403)

    planejamento = Planejamento.query.get_or_404(plano_id)
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)

    titulo = request.form.get('titulo', '').strip()
    descricao = request.form.get('descricao', '').strip()
    responsaveis_ids = request.form.getlist('responsaveis', type=int)
    prazo_str = request.form.get('prazo', '').strip()
    status = request.form.get('status', 'backlog', type=str)
    if status not in STATUS_ACAO:
        status = 'backlog'

    if not titulo:
        flash('Título da ação é obrigatório.', 'danger')
        return redirect(url_for('planejamentos.listar', expand=plano_id))

    usuarios_unidade = {u.id for u in _usuarios_unidade(planejamento.unidade_id)}
    responsaveis_ids = [rid for rid in responsaveis_ids if rid in usuarios_unidade]

    empresas_ids = request.form.getlist('empresas', type=int)
    from app.models.empresa import EmpresaContratada
    empresas_ativas = {e.id for e in EmpresaContratada.query.filter_by(ativo=True).all()}
    empresas_ids = [eid for eid in empresas_ids if eid in empresas_ativas]

    from sqlalchemy import func
    ultima = db.session.query(func.max(AcaoPlanejamento.ordem)).filter_by(planejamento_id=plano_id).scalar()
    ultima_ordem = (ultima or 0)

    from app.models.usuario import Usuario

    from datetime import datetime as dt
    prazo = None
    if prazo_str:
        try:
            prazo = dt.strptime(prazo_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    acao = AcaoPlanejamento(
        plano_id=plano_id,
        titulo=titulo,
        descricao=descricao or None,
        status=status,
        ordem=ultima_ordem + 1,
        prazo=prazo,
        criado_por=current_user.id,
    )
    db.session.add(acao)
    db.session.flush()

    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id

    for uid in responsaveis_ids:
        usr = Usuario.query.get(uid)
        if usr:
            acao.responsaveis.append(usr)
    for eid in empresas_ids:
        emp = EmpresaContratada.query.get(eid)
        if emp:
            acao.empresas.append(emp)

    db.session.commit()
    flash('Ação adicionada.', 'success')
    return redirect(url_for('planejamentos.listar', expand=plano_id))


@planejamentos_bp.route('/acoes/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status_acao(id):
    if not current_user.pode('alterar_status_acao'):
        abort(403)

    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)

    status = request.form.get('status', '').strip()
    if status not in STATUS_ACAO:
        return jsonify({'ok': False, 'erro': 'Status inválido'}), 400

    acao.status = status
    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id
    db.session.commit()

    acoes_flat = list(planejamento.acoes.order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id))
    total = len(acoes_flat)
    concluidas = sum(1 for a in acoes_flat if a.status == 'concluido')
    canceladas = sum(1 for a in acoes_flat if a.status == 'cancelado')
    em_andamento = sum(1 for a in acoes_flat if a.status == 'em_andamento')
    pendentes = sum(1 for a in acoes_flat if a.status == 'backlog')
    hoje = date.today()
    atrasadas = sum(1 for a in acoes_flat if a.status not in ('concluido', 'cancelado') and a.prazo and a.prazo < hoje)
    total_ativas = total - canceladas
    progresso_pct = round(100 * concluidas / total_ativas) if total_ativas else 0
    em_andamento_pct = round(100 * em_andamento / total_ativas) if total_ativas else 0
    pendentes_pct = round(100 * pendentes / total_ativas) if total_ativas else 0
    return jsonify({
        'ok': True,
        'status_resumo': {'atrasadas': atrasadas, 'em_andamento': em_andamento, 'pendentes': pendentes, 'concluidas': concluidas, 'canceladas': canceladas},
        'progresso_pct': progresso_pct,
        'em_andamento_pct': em_andamento_pct,
        'pendentes_pct': pendentes_pct,
    })


@planejamentos_bp.route('/acoes/<int:id>/responsaveis', methods=['POST'])
@login_required
def atualizar_responsaveis(id):
    if not current_user.pode('criar_acao'):
        abort(403)

    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)

    from app.models.usuario import Usuario
    from app.models.empresa import EmpresaContratada

    responsaveis_ids = request.form.getlist('responsaveis', type=int)
    usuarios_unidade = {u.id for u in _usuarios_unidade(planejamento.unidade_id)}
    responsaveis_ids = [rid for rid in responsaveis_ids if rid in usuarios_unidade]
    acao.responsaveis = Usuario.query.filter(Usuario.id.in_(responsaveis_ids)).all()

    empresas_ids = request.form.getlist('empresas', type=int)
    empresas_ativas = {e.id for e in EmpresaContratada.query.filter_by(ativo=True).all()}
    empresas_ids = [eid for eid in empresas_ids if eid in empresas_ativas]
    acao.empresas = EmpresaContratada.query.filter(EmpresaContratada.id.in_(empresas_ids)).all()

    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    html = _resp_display_html(acao)
    return jsonify({'ok': True, 'html': html})


@planejamentos_bp.route('/acoes/<int:id>/prazo', methods=['POST'])
@login_required
def atualizar_prazo_acao(id):
    if not current_user.pode('criar_acao'):
        abort(403)

    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)

    prazo_str = request.form.get('prazo', '').strip()
    prazo = None
    if prazo_str:
        try:
            from datetime import datetime as dt
            prazo = dt.strptime(prazo_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    acao.prazo = prazo
    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    return jsonify({'ok': True})


@planejamentos_bp.route('/acoes/<int:id>/observacao', methods=['POST'])
@login_required
def criar_observacao(id):
    """Adiciona observação em uma ação (HTML + anexos)."""
    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)
    texto = request.form.get('texto', '').strip()
    # Quill pode enviar <p><br></p> vazio
    if not texto or texto in ('<p><br></p>', '<p></p>'):
        return jsonify({'ok': False, 'erro': 'Texto é obrigatório'}), 400
    texto = _links_nova_aba(texto)
    obs = AcaoObservacao(
        acao_id=id,
        usuario_id=current_user.id,
        texto=texto,
    )
    db.session.add(obs)
    db.session.flush()
    for f in request.files.getlist('anexos')[:10]:
        if f and f.filename:
            conteudo = f.read()
            f.seek(0)
            if len(conteudo) / (1024 * 1024) <= _MAX_MB:
                anexo = _salvar_obs_anexo(f, obs.id)
                if anexo:
                    db.session.add(anexo)
    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    _br = obs.criado_em + timedelta(hours=-3) if obs.criado_em else None
    anexos_list = [
        {'original': a.original, 'url': a.url, 'eh_imagem': a.eh_imagem}
        for a in obs.anexos
    ]
    primeiro_nome = ((current_user.nome or '').split() + ['?'])[0]
    return jsonify({
        'ok': True,
        'id': obs.id,
        'texto': obs.texto,
        'criado_em': _br.strftime('%d/%m/%Y %H:%M') if _br else '',
        'autor': current_user.nome,
        'autor_primeiro': primeiro_nome,
        'autor_foto_url': current_user.foto_url if hasattr(current_user, 'foto_url') else None,
        'autor_inicial': current_user.inicial if hasattr(current_user, 'inicial') else (primeiro_nome[:1].upper() or '?'),
        'anexos': anexos_list,
    })


@planejamentos_bp.route('/<int:plano_id>/acoes/reordenar', methods=['POST'])
@login_required
def reordenar_acoes(plano_id):
    """Reordena ações do planejamento (drag-and-drop)."""
    planejamento = Planejamento.query.get_or_404(plano_id)
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)
    if not current_user.pode('criar_acao'):
        abort(403)
    ordem_ids = request.json.get('ids', [])
    acao_ids_planos = {a.id: a for a in AcaoPlanejamento.query.filter(
        AcaoPlanejamento.id.in_(ordem_ids),
        AcaoPlanejamento.planejamento_id == plano_id,
    ).all()}
    for ordem, acao_id in enumerate(ordem_ids):
        acao = acao_ids_planos.get(acao_id)
        if acao:
            acao.ordem = ordem
    planejamento.atualizado_em = datetime.utcnow()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    return jsonify({'ok': True})


@planejamentos_bp.route('/imprimir/projeto/<int:plano_id>')
@login_required
def imprimir_projeto(plano_id):
    """Impressão de um único projeto (ações + observações)."""
    planejamento = Planejamento.query.get_or_404(plano_id)
    ids = _ids_unidades_usuario()
    if planejamento.unidade_id not in ids:
        abort(403)
    acoes_flat = list(planejamento.acoes.order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id))
    total = len(acoes_flat)
    concluidas = sum(1 for a in acoes_flat if a.status == 'concluido')
    canceladas = sum(1 for a in acoes_flat if a.status == 'cancelado')
    em_andamento = sum(1 for a in acoes_flat if a.status == 'em_andamento')
    pendentes = sum(1 for a in acoes_flat if a.status == 'backlog')
    total_ativas = total - canceladas
    progresso_pct = round(100 * concluidas / total_ativas) if total_ativas else 0
    em_andamento_pct = round(100 * em_andamento / total_ativas) if total_ativas else 0
    pendentes_pct = round(100 * pendentes / total_ativas) if total_ativas else 0
    obs_list = []
    for acao in acoes_flat:
        for obs in acao.observacoes:
            obs_list.append({'obs': obs, 'acao_titulo': acao.titulo})
    obs_list.sort(key=lambda x: x['obs'].criado_em or datetime.min)
    planejamentos_dados = [{
        'plano': planejamento,
        'acoes_flat': acoes_flat,
        'progresso_pct': progresso_pct,
        'em_andamento_pct': em_andamento_pct,
        'pendentes_pct': pendentes_pct,
        'observacoes_ordenadas': obs_list,
    }]
    return render_template(
        'planejamentos/imprimir.html',
        planejamentos_dados=planejamentos_dados,
        unidade_filtro=None,
        unidades=[],
        now=datetime.utcnow(),
    )


def _status_plano_imprimir(p):
    """Retorna 'abertos', 'concluidos' ou 'cancelados' para filtro de impressão."""
    acoes = list(p.acoes.all())
    total = len(acoes)
    if total == 0:
        return 'abertos'
    canceladas = sum(1 for a in acoes if a.status == 'cancelado')
    em_andamento = sum(1 for a in acoes if a.status == 'em_andamento')
    pendentes = sum(1 for a in acoes if a.status == 'backlog')
    concluidas = sum(1 for a in acoes if a.status == 'concluido')
    if canceladas == total:
        return 'cancelados'
    if em_andamento or pendentes:
        return 'abertos'
    if concluidas > 0:
        return 'concluidos'
    return 'abertos'


@planejamentos_bp.route('/imprimir')
@planejamentos_bp.route('/imprimir/unidade/<int:unidade_id>')
@login_required
def imprimir(unidade_id=None):
    """Página de impressão do planejamento (todos, por unidade e/ou por aba)."""
    ids = _ids_unidades_usuario()
    if not ids:
        flash('Você precisa estar vinculado a pelo menos uma unidade.', 'warning')
        return redirect(url_for('planejamentos.listar'))
    aba = request.args.get('aba', 'abertos')
    if aba not in ('abertos', 'concluidos', 'cancelados'):
        aba = 'abertos'
    from app.models.unidade import Unidade
    q = Planejamento.query.filter(Planejamento.unidade_id.in_(ids))
    if unidade_id and unidade_id in ids:
        q = q.filter(Planejamento.unidade_id == unidade_id)
    planejamentos = q.order_by(
        db.desc(Planejamento.gravidade * Planejamento.urgencia * Planejamento.tendencia),
        Planejamento.titulo,
    ).all()
    planejamentos = [p for p in planejamentos if _status_plano_imprimir(p) == aba]
    planejamentos_dados = []
    for p in planejamentos:
        acoes_flat = list(p.acoes.order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id))
        total = len(acoes_flat)
        concluidas = sum(1 for a in acoes_flat if a.status == 'concluido')
        canceladas = sum(1 for a in acoes_flat if a.status == 'cancelado')
        em_andamento = sum(1 for a in acoes_flat if a.status == 'em_andamento')
        pendentes = sum(1 for a in acoes_flat if a.status == 'backlog')
        total_ativas = total - canceladas
        progresso_pct = round(100 * concluidas / total_ativas) if total_ativas else 0
        em_andamento_pct = round(100 * em_andamento / total_ativas) if total_ativas else 0
        pendentes_pct = round(100 * pendentes / total_ativas) if total_ativas else 0
        planejamentos_dados.append({
            'plano': p,
            'acoes_flat': acoes_flat,
            'progresso_pct': progresso_pct,
            'em_andamento_pct': em_andamento_pct,
            'pendentes_pct': pendentes_pct,
        })
    unidades = Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()
    titulo_impresso = {'abertos': 'Planos em Aberto', 'concluidos': 'Planos Concluídos', 'cancelados': 'Planos Cancelados'}.get(aba, 'Planejamentos')
    return render_template(
        'planejamentos/imprimir_resumo.html',
        planejamentos_dados=planejamentos_dados,
        unidade_filtro=Unidade.query.get(unidade_id) if unidade_id else None,
        unidades=unidades,
        aba=aba,
        titulo_impresso=titulo_impresso,
        now=datetime.utcnow(),
    )
