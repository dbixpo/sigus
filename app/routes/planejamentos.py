# -*- coding: utf-8 -*-
"""Planejamentos/Projetos com Kanban e GUT — estilo Monday.com."""
import os
import uuid
import mimetypes
from datetime import datetime, timedelta, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, selectinload, noload

from app import db
from app.utils import agora_local, formatar_brasilia, hoje_brasilia
from app.models.planejamento import (
    Planejamento, AcaoPlanejamento, AcaoObservacao, AcaoObservacaoAnexo,
    PlanejamentoAnexo, STATUS_ACAO, STATUS_ACAO_LABELS,
    planejamento_unidades, planejamento_tipos_unidade,
)

# Evita reprocessar alertas de prazo em todo GET da listagem (1x/dia por worker).
_ALERTAS_PRAZO_DIA = {'data': None}

planejamentos_bp = Blueprint('planejamentos', __name__, url_prefix='/planejamentos')

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'planos')
_UPLOAD_DIR_OBS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'obs_acoes')
_MAX_MB = 100

# Tipos de arquivos permitidos nos anexos de planejamentos/observações.
# Mantém imagens e PDF e adiciona formatos comuns de documentos, planilhas e apresentações.
_ALLOWED = (
    'image/',                          # Imagens (jpg, png, gif, webp, etc.)
    'application/pdf',                 # PDF
    'audio/',                          # Audio (mp3, ogg, etc.)
    'application/ogg',                 # OGG muitas vezes vem assim no upload (não só audio/ogg)
    'video/ogg',                       # alguns browsers para ficheiro .ogg
    'application/msword',              # .doc
    'application/vnd.openxmlformats-officedocument',  # .docx, .xlsx, .pptx
    'application/vnd.ms-excel',        # .xls
    'application/vnd.ms-powerpoint',   # .ppt
    'application/vnd.oasis.opendocument',  # .odt, .ods, .odp, etc.
    'text/plain',                      # .txt
    'text/csv',                        # .csv
    'application/csv',                 # .csv (alguns clientes)
    'application/zip',                 # .zip
    'application/x-zip-compressed',    # .zip (Windows/IE/alguns browsers)
    'application/vnd.rar',             # .rar
    'application/x-rar-compressed',    # .rar (comum)
    'message/rfc822',                  # .eml (e-mail) quando o MIME já vem correto
)


def _salvar_anexo(file_obj, planejamento_id):
    """Salva PDF ou imagem e retorna PlanejamentoAnexo."""
    original = file_obj.filename or 'sem_nome'
    mime = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    ext = os.path.splitext(original)[1].lower() or '.bin'
    # .eml (Thunderbird/Outlook) normalmente vem como message/rfc822 (ou às vezes octet-stream)
    if ext == '.eml':
        if mime in ('application/octet-stream', 'text/plain', 'application/octetstream'):
            mime = 'message/rfc822'
    elif ext in ('.ogg', '.oga', '.opus'):
        if mime in ('application/octet-stream', 'application/ogg', 'video/ogg'):
            mime = 'audio/ogg'
    elif ext == '.csv':
        if mime in ('application/octet-stream', 'text/plain', 'application/octetstream'):
            mime = 'text/csv'
    elif ext == '.zip':
        if mime in ('application/octet-stream', 'application/octetstream'):
            mime = 'application/zip'
    elif ext == '.rar':
        if mime in ('application/octet-stream', 'application/octetstream'):
            mime = 'application/vnd.rar'
    elif not any(mime.startswith(p) for p in _ALLOWED):
        return None
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
    ext = os.path.splitext(original)[1].lower() or '.bin'
    if ext == '.eml':
        if mime in ('application/octet-stream', 'text/plain', 'application/octetstream'):
            mime = 'message/rfc822'
    elif ext in ('.ogg', '.oga', '.opus'):
        if mime in ('application/octet-stream', 'application/ogg', 'video/ogg'):
            mime = 'audio/ogg'
    elif ext == '.csv':
        if mime in ('application/octet-stream', 'text/plain', 'application/octetstream'):
            mime = 'text/csv'
    elif ext == '.zip':
        if mime in ('application/octet-stream', 'application/octetstream'):
            mime = 'application/zip'
    elif ext == '.rar':
        if mime in ('application/octet-stream', 'application/octetstream'):
            mime = 'application/vnd.rar'
    elif not any(mime.startswith(p) for p in _ALLOWED):
        return None
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(_UPLOAD_DIR_OBS, exist_ok=True)
    file_obj.save(os.path.join(_UPLOAD_DIR_OBS, filename))
    return AcaoObservacaoAnexo(
        observacao_id=observacao_id, filename=filename, original=original, mime_type=mime
    )


def _ids_unidades_usuario():
    """IDs das unidades às quais o usuário está vinculado.

    Observação: mesmo perfis com permissão de 'ver_todas_unidades' enxergam
    aqui apenas as unidades em que estão vinculados. Isso garante que os
    planejamentos sejam sempre restritos às unidades do próprio usuário.
    """
    return [u.id for u in current_user.unidades_ativas]


def _ids_unidades_planejamento(planejamento):
    """IDs de todas as unidades associadas ao planejamento (principal + vinculadas + tipos)."""
    from app.models.unidade import Unidade
    ids = {planejamento.unidade_id}
    for u in planejamento.unidades.all():
        ids.add(u.id)
    for tipo in planejamento.tipos_unidade.all():
        for u in Unidade.query.filter_by(tipo_unidade_id=tipo.id, status='ativa').all():
            ids.add(u.id)
    return ids


def _unidades_do_planejamento(planejamento):
    """Lista de Unidade que participam do planejamento (origem + vinculadas + por tipo), ordenada por nome."""
    from app.models.unidade import Unidade
    ids = _ids_unidades_planejamento(planejamento)
    return Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()


def _usuario_pode_editar_planejamento(planejamento):
    """Verifica se o usuário tem alguma unidade em comum com o planejamento."""
    ids_usuario = set(_ids_unidades_usuario())
    ids_plano = _ids_unidades_planejamento(planejamento)
    return bool(ids_usuario & ids_plano)


def _usuarios_unidade(unidade_id):
    """Usuários vinculados à unidade (para atribuir responsáveis)."""
    from app.models.unidade import UsuarioUnidade
    vincs = UsuarioUnidade.query.filter_by(unidade_id=unidade_id, ativo=True).all()
    usuarios = [v.usuario for v in vincs if v.usuario]
    return sorted(usuarios, key=lambda u: (u.nome or '').lower())


def _mapa_unidades_planejamentos(planejamentos):
    """plano_id -> set(unidade_id) sem N+1."""
    from app.models.unidade import Unidade
    mapa = {p.id: {p.unidade_id} for p in planejamentos}
    pids = list(mapa)
    if not pids:
        return mapa

    for pid, uid in db.session.query(
        planejamento_unidades.c.planejamento_id,
        planejamento_unidades.c.unidade_id,
    ).filter(planejamento_unidades.c.planejamento_id.in_(pids)):
        mapa.setdefault(pid, set()).add(uid)

    tipo_rows = db.session.query(
        planejamento_tipos_unidade.c.planejamento_id,
        planejamento_tipos_unidade.c.tipo_unidade_id,
    ).filter(planejamento_tipos_unidade.c.planejamento_id.in_(pids)).all()
    tipo_ids = {tid for _, tid in tipo_rows if tid}
    unidades_por_tipo = {}
    if tipo_ids:
        for u in Unidade.query.filter(
            Unidade.tipo_unidade_id.in_(tipo_ids),
            Unidade.status == 'ativa',
        ).all():
            unidades_por_tipo.setdefault(u.tipo_unidade_id, []).append(u.id)
    for pid, tid in tipo_rows:
        for uid in unidades_por_tipo.get(tid, []):
            mapa.setdefault(pid, set()).add(uid)
    return mapa


def _usuarios_por_planejamentos(planejamentos):
    """plano_id -> lista de Usuario (ordenado), em poucas queries."""
    from app.models.unidade import UsuarioUnidade
    from app.models.usuario import Usuario

    mapa_u = _mapa_unidades_planejamentos(planejamentos)
    all_unidade_ids = set()
    for ids in mapa_u.values():
        all_unidade_ids |= ids

    users_by_id = {}
    usuarios_por_unidade = {}
    if all_unidade_ids:
        vincs = UsuarioUnidade.query.filter(
            UsuarioUnidade.unidade_id.in_(all_unidade_ids),
            UsuarioUnidade.ativo.is_(True),
        ).all()
        user_ids = {v.usuario_id for v in vincs if v.usuario_id}
        if user_ids:
            users_by_id = {
                u.id: u for u in Usuario.query.filter(Usuario.id.in_(user_ids)).all()
            }
        for v in vincs:
            if v.usuario_id and v.usuario_id in users_by_id:
                usuarios_por_unidade.setdefault(v.unidade_id, set()).add(v.usuario_id)

    result = {}
    for p in planejamentos:
        ids = set()
        for uid in mapa_u.get(p.id, ()):
            ids |= usuarios_por_unidade.get(uid, set())
        result[p.id] = sorted(
            (users_by_id[i] for i in ids if i in users_by_id),
            key=lambda u: (u.nome or '').lower(),
        )
    return result


def _usuarios_planejamento(planejamento):
    """Usuários de todas as unidades vinculadas ao planejamento."""
    return _usuarios_por_planejamentos([planejamento]).get(planejamento.id, [])


def _gerar_alertas_prazos():
    """Cria notificações de prazo (hoje / em 3 dias) no máx. 1x por dia por worker.

    Antes rodava em todo GET de /planejamentos/ com N queries por usuário — isso
    deixava a listagem lenta. Agora usa poucas queries em lote.
    """
    hoje = hoje_brasilia()
    if _ALERTAS_PRAZO_DIA.get('data') == hoje:
        return

    from app.models.notificacao import Notificacao

    tres_dias = hoje + timedelta(days=3)
    acoes = (
        AcaoPlanejamento.query.options(
            selectinload(AcaoPlanejamento.responsaveis),
            joinedload(AcaoPlanejamento.planejamento),
        )
        .filter(
            AcaoPlanejamento.status.notin_(['concluido', 'cancelado']),
            AcaoPlanejamento.prazo.in_([hoje, tres_dias]),
        )
        .all()
    )
    if not acoes:
        _ALERTAS_PRAZO_DIA['data'] = hoje
        return

    planos = []
    vistos = set()
    for a in acoes:
        p = a.planejamento
        if p and p.id not in vistos:
            vistos.add(p.id)
            planos.append(p)
    usuarios_por_plano = _usuarios_por_planejamentos(planos)

    candidatos = []  # (usuario_id, titulo, texto)
    for acao in acoes:
        plano = acao.planejamento
        if not plano:
            continue
        dias = 0 if acao.prazo == hoje else 3
        responsaveis_nomes = []
        for r in acao.responsaveis or []:
            if r and r.nome:
                responsaveis_nomes.append(r.nome.split()[0])
        resp_txt = ', '.join(responsaveis_nomes) if responsaveis_nomes else '—'
        titulo = 'Ação vence hoje' if dias == 0 else 'Ação vence em 3 dias'
        texto = f'Plano: "{plano.titulo}" — Ação: "{acao.titulo}" — Responsável(is): {resp_txt}'
        for usuario in usuarios_por_plano.get(plano.id, []):
            if usuario and usuario.id:
                candidatos.append((usuario.id, titulo, texto))

    if not candidatos:
        _ALERTAS_PRAZO_DIA['data'] = hoje
        return

    user_ids = {c[0] for c in candidatos}
    existentes = set(
        db.session.query(
            Notificacao.usuario_id, Notificacao.titulo, Notificacao.texto
        )
        .filter(
            Notificacao.tipo == 'alerta_planejamento',
            Notificacao.usuario_id.in_(user_ids),
        )
        .all()
    )
    novos = []
    ja = set(existentes)
    for item in candidatos:
        if item in ja:
            continue
        ja.add(item)
        novos.append(Notificacao(
            usuario_id=item[0],
            tipo='alerta_planejamento',
            titulo=item[1],
            texto=item[2],
        ))
    if novos:
        db.session.add_all(novos)
    _ALERTAS_PRAZO_DIA['data'] = hoje


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
        foto = f'<img src="{e.foto_url}" alt="" class="resp-avatar">' if e.foto_url else '<span class="resp-inicial resp-empresa"><i class="fas fa-building"></i></span>'
        parts.append(f'<div class="resp-item" title="{e.razao_social or ""}">{foto}<span class="resp-nome">{nome}</span></div>')
    if not parts:
        return '<span class="text-muted">—</span>'
    return '<div class="d-flex flex-wrap align-items-center gap-1">' + ''.join(parts) + '</div>'


@planejamentos_bp.route('/')
@login_required
def listar():
    from app.models.unidade import Unidade
    from app.models.planejamento import acacao_planejamento_responsaveis, STATUS_ACAO_LABELS
    from app.models.planejamento import planejamento_unidades, planejamento_tipos_unidade
    from app.models.tipo_unidade import TipoUnidade

    ids = _ids_unidades_usuario()
    if not ids:
        flash('Você precisa estar vinculado a pelo menos uma unidade para acessar os planejamentos.', 'warning')
        return redirect(url_for('dashboard.index'))

    unidade_id = request.args.get('unidade_id', type=int)
    aba = request.args.get('aba', 'abertos')
    if aba not in ('abertos', 'concluidos', 'cancelados'):
        aba = 'abertos'
    expand_id = request.args.get('expand', type=int)
    if unidade_id and unidade_id not in ids:
        unidade_id = None
    # Se não veio unidade pela URL:
    # - para não-administrador, tenta usar a unidade_principal
    # - se ainda assim não tiver (ou não estiver em ids) e só houver 1 unidade, usa essa
    if unidade_id is None and not current_user.perfil == 'administrador':
        if getattr(current_user, 'unidade_principal', None) is not None:
            up_id = current_user.unidade_principal.id
            if up_id in ids:
                unidade_id = up_id
        if unidade_id is None and len(ids) == 1:
            unidade_id = ids[0]

    unidades = Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()

    # Busca planejamentos vinculados a unidades específicas OU a tipos de unidades que o usuário tem acesso
    # IDs de tipos de unidades das unidades do usuário
    tipos_unidade_ids = db.session.query(Unidade.tipo_unidade_id).filter(
        Unidade.id.in_(ids),
        Unidade.status == 'ativa',
        Unidade.tipo_unidade_id.isnot(None)
    ).distinct().all()
    tipos_unidade_ids = [t[0] for t in tipos_unidade_ids if t[0]]
    
    # Coleta todos os IDs de planejamentos relevantes
    planejamento_ids = set()
    
    # Planejamentos com unidade_id nas unidades do usuário
    planej_ids_1 = db.session.query(Planejamento.id).filter(Planejamento.unidade_id.in_(ids)).all()
    planejamento_ids.update([p[0] for p in planej_ids_1])
    
    # Planejamentos vinculados a unidades específicas que o usuário tem acesso
    planej_ids_2 = db.session.query(planejamento_unidades.c.planejamento_id).filter(
        planejamento_unidades.c.unidade_id.in_(ids)
    ).all()
    planejamento_ids.update([p[0] for p in planej_ids_2])
    
    # Planejamentos vinculados a tipos de unidades que o usuário tem acesso
    if tipos_unidade_ids:
        planej_ids_3 = db.session.query(planejamento_tipos_unidade.c.planejamento_id).filter(
            planejamento_tipos_unidade.c.tipo_unidade_id.in_(tipos_unidade_ids)
        ).all()
        planejamento_ids.update([p[0] for p in planej_ids_3])
    
    # Filtra por unidade específica se selecionada
    if unidade_id:
        planejamento_ids_filtrado = set()
        unidade_obj = Unidade.query.get(unidade_id)
        tipo_unidade_id = unidade_obj.tipo_unidade_id if unidade_obj else None
        
        # Planejamentos da unidade específica
        planej_ids_u1 = db.session.query(Planejamento.id).filter(Planejamento.unidade_id == unidade_id).all()
        planejamento_ids_filtrado.update([p[0] for p in planej_ids_u1])
        
        # Planejamentos vinculados a essa unidade
        planej_ids_u2 = db.session.query(planejamento_unidades.c.planejamento_id).filter(
            planejamento_unidades.c.unidade_id == unidade_id
        ).all()
        planejamento_ids_filtrado.update([p[0] for p in planej_ids_u2])
        
        # Planejamentos vinculados ao tipo dessa unidade
        if tipo_unidade_id:
            planej_ids_u3 = db.session.query(planejamento_tipos_unidade.c.planejamento_id).filter(
                planejamento_tipos_unidade.c.tipo_unidade_id == tipo_unidade_id
            ).all()
            planejamento_ids_filtrado.update([p[0] for p in planej_ids_u3])
        
        planejamento_ids = planejamento_ids_filtrado
    
    # Busca os planejamentos pelos IDs coletados
    # Nota: acoes, unidades e tipos_unidade usam lazy='dynamic', não permitem joinedload
    if planejamento_ids:
        q = Planejamento.query.options(
            joinedload(Planejamento.unidade),
            joinedload(Planejamento.criador),
            joinedload(Planejamento.ultimo_editor),
        ).filter(Planejamento.id.in_(planejamento_ids))
        q = q.order_by(
            db.desc(Planejamento.gravidade * Planejamento.urgencia * Planejamento.tendencia),
            Planejamento.titulo,
        )
        planejamentos_todos = q.all()
    else:
        planejamentos_todos = []

    status_por_plano = {}
    # Contagem por aba: só id/status (sem carregar M2M nem observações)
    if planejamentos_todos:
        all_ids = [p.id for p in planejamentos_todos]
        status_rows = db.session.query(
            AcaoPlanejamento.planejamento_id,
            AcaoPlanejamento.status,
        ).filter(AcaoPlanejamento.planejamento_id.in_(all_ids)).all()
        acoes_status_por_plano = {}
        for pid, st in status_rows:
            acoes_status_por_plano.setdefault(pid, []).append(st)

        for p in planejamentos_todos:
            statuses = acoes_status_por_plano.get(p.id, [])
            total = len(statuses)
            if total == 0:
                status_por_plano[p.id] = 'abertos'
                continue
            canceladas = sum(1 for s in statuses if s == 'cancelado')
            em_andamento = sum(1 for s in statuses if s == 'em_andamento')
            pendentes = sum(1 for s in statuses if s == 'backlog')
            if canceladas == total:
                status_por_plano[p.id] = 'cancelados'
            elif em_andamento or pendentes:
                status_por_plano[p.id] = 'abertos'
            else:
                status_por_plano[p.id] = 'concluidos'

    contagem_por_aba = {'abertos': 0, 'concluidos': 0, 'cancelados': 0}
    for st in status_por_plano.values():
        contagem_por_aba[st] = contagem_por_aba.get(st, 0) + 1

    planejamentos = [p for p in planejamentos_todos if status_por_plano.get(p.id) == aba]

    # Ações completas só da aba atual (sem observações — carregam no expand via AJAX)
    planejamentos_dados = []
    planej_ids = [p.id for p in planejamentos]
    contagem_acoes_usuario = {}
    ids_com_minhas_acoes = set()
    acoes_por_plano = {}

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

        acoes_aba = (
            AcaoPlanejamento.query.options(
                selectinload(AcaoPlanejamento.responsaveis),
                selectinload(AcaoPlanejamento.empresas),
                noload(AcaoPlanejamento.observacoes),
            )
            .filter(AcaoPlanejamento.planejamento_id.in_(planej_ids))
            .order_by(AcaoPlanejamento.planejamento_id, AcaoPlanejamento.ordem, AcaoPlanejamento.id)
            .all()
        )
        for ac in acoes_aba:
            acoes_por_plano.setdefault(ac.planejamento_id, []).append(ac)

    hoje = hoje_brasilia()
    tres_dias = hoje + timedelta(days=3)

    # Banner de prazos (leve) + geração de sininho no máx. 1x/dia por worker
    acoes_vencendo = []
    if planejamentos_todos:
        planos_dict = {p.id: p for p in planejamentos_todos}
        planej_ids_todos = list(planos_dict)
        acoes_proximas = (
            AcaoPlanejamento.query.options(
                selectinload(AcaoPlanejamento.responsaveis),
            )
            .filter(
                AcaoPlanejamento.planejamento_id.in_(planej_ids_todos),
                AcaoPlanejamento.status.notin_(['concluido', 'cancelado']),
                AcaoPlanejamento.prazo.in_([hoje, tres_dias]),
            )
            .all()
        )
        for acao in acoes_proximas:
            plano = planos_dict.get(acao.planejamento_id)
            if not plano:
                continue
            dias = 0 if acao.prazo == hoje else 3
            acoes_vencendo.append({'acao': acao, 'plano': plano, 'dias': dias})
        try:
            _gerar_alertas_prazos()
        except Exception:
            # Listagem não deve falhar por alerta do sininho
            db.session.rollback()

    from app.models.empresa import EmpresaContratada
    empresas_ativas = EmpresaContratada.query.filter_by(ativo=True).order_by(EmpresaContratada.razao_social).all()
    usuarios_por_plano = _usuarios_por_planejamentos(planejamentos) if planejamentos else {}

    for p in planejamentos:
        acoes_flat = acoes_por_plano.get(p.id, [])
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

        proxima_acao = None
        for acao in acoes_flat:
            if acao.status not in ('concluido', 'cancelado'):
                proxima_acao = acao
                break

        planejamentos_dados.append({
            'plano': p,
            'acoes_flat': acoes_flat,
            'progresso_pct': progresso_pct,
            'em_andamento_pct': em_andamento_pct,
            'pendentes_pct': pendentes_pct,
            'usuarios': usuarios_por_plano.get(p.id, []),
            'empresas': empresas_ativas,
            'proxima_acao': proxima_acao,
            'status_resumo': {'atrasadas': atrasadas, 'pendentes': pendentes, 'em_andamento': em_andamento, 'concluidas': concluidas, 'canceladas': canceladas},
        })

    # Evita N+1 no template: carrega unidades/tipos/anexos em lote para os planos exibidos
    unidades_vinc_por_plano = {pid: [] for pid in planej_ids}
    tipos_vinc_por_plano = {pid: [] for pid in planej_ids}
    anexos_por_plano = {pid: [] for pid in planej_ids}
    if planej_ids:
        # Unidades vinculadas explicitamente
        rows_u = (
            db.session.query(planejamento_unidades.c.planejamento_id, Unidade)
            .join(Unidade, Unidade.id == planejamento_unidades.c.unidade_id)
            .filter(planejamento_unidades.c.planejamento_id.in_(planej_ids))
            .order_by(planejamento_unidades.c.planejamento_id, Unidade.nome)
            .all()
        )
        for pid, u in rows_u:
            if pid in unidades_vinc_por_plano:
                unidades_vinc_por_plano[pid].append(u)

        # Tipos de unidade vinculados
        rows_t = (
            db.session.query(planejamento_tipos_unidade.c.planejamento_id, TipoUnidade)
            .join(TipoUnidade, TipoUnidade.id == planejamento_tipos_unidade.c.tipo_unidade_id)
            .filter(planejamento_tipos_unidade.c.planejamento_id.in_(planej_ids))
            .order_by(planejamento_tipos_unidade.c.planejamento_id, TipoUnidade.nome)
            .all()
        )
        for pid, t in rows_t:
            if pid in tipos_vinc_por_plano:
                tipos_vinc_por_plano[pid].append(t)

        # Anexos do plano
        rows_a = (
            PlanejamentoAnexo.query.filter(PlanejamentoAnexo.planejamento_id.in_(planej_ids))
            .order_by(PlanejamentoAnexo.planejamento_id, PlanejamentoAnexo.criado_em.asc())
            .all()
        )
        for a in rows_a:
            if a.planejamento_id in anexos_por_plano:
                anexos_por_plano[a.planejamento_id].append(a)

        for d in planejamentos_dados:
            pid = d['plano'].id
            d['unidades_vinculadas'] = unidades_vinc_por_plano.get(pid, [])
            d['tipos_vinculados'] = tipos_vinc_por_plano.get(pid, [])
            d['anexos'] = anexos_por_plano.get(pid, [])

    tem_planos_geral = len(planejamentos_todos) > 0
    filtro_inicial = request.args.get('filtro', '')
    somente_minhas_inicial = request.args.get('somente_minhas', '')
    return render_template(
        'planejamentos/listar.html',
        planejamentos_dados=planejamentos_dados,
        unidades=unidades,
        unidade_id=unidade_id,
        aba=aba,
        filtro_inicial=filtro_inicial,
        somente_minhas_inicial=somente_minhas_inicial,
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
        acoes_vencendo=acoes_vencendo,
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
    from app.models.tipo_unidade import TipoUnidade
    # Para o formulário, mostra todas as unidades ativas (não apenas as vinculadas)
    unidades = Unidade.query.filter(Unidade.status == 'ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        unidade_id = request.form.get('unidade_id', type=int)  # Unidade principal (mantida para compatibilidade)
        # Campos hidden enviam valores separados por vírgula (ex: "1,56")
        unidades_ids_str = request.form.get('unidades_ids', '').strip()
        tipos_unidade_ids_str = request.form.get('tipos_unidade_ids', '').strip()
        unidades_ids = [int(x) for x in unidades_ids_str.split(',') if x.strip() and x.strip().isdigit()]
        tipos_unidade_ids = [int(x) for x in tipos_unidade_ids_str.split(',') if x.strip() and x.strip().isdigit()]
        g = request.form.get('gravidade', 1, type=int)
        u = request.form.get('urgencia', 1, type=int)
        t = request.form.get('tendencia', 1, type=int)

        if not titulo:
            flash('Título é obrigatório.', 'danger')
            return redirect(url_for('planejamentos.criar'))

        # Se não selecionou unidades nem tipos, usa a unidade principal
        if not unidades_ids and not tipos_unidade_ids:
            if not unidade_id or unidade_id not in ids:
                flash('Selecione pelo menos uma unidade ou tipo de unidade.', 'danger')
                return redirect(url_for('planejamentos.criar'))
            unidades_ids = [unidade_id]

        # Valida: a unidade origem (primeira) deve ser do usuário; as demais podem ser qualquer unidade ativa (compartilhar)
        if unidades_ids:
            if unidades_ids[0] not in ids:
                abort(403)

        g = max(1, min(5, g))
        u = max(1, min(5, u))
        t = max(1, min(5, t))

        now = agora_local()
        # Usa a primeira unidade selecionada como unidade principal, ou a unidade_id se não houver seleção
        unidade_principal_id = unidades_ids[0] if unidades_ids else unidade_id
        planejamento = Planejamento(
            unidade_id=unidade_principal_id,
            titulo=titulo,
            descricao=descricao or None,
            gravidade=g, urgencia=u, tendencia=t,
            criado_por=current_user.id,
            atualizado_em=now,
            atualizado_por=current_user.id,
        )
        db.session.add(planejamento)
        db.session.flush()

        # Adiciona unidades selecionadas
        if unidades_ids:
            unidades_objs = Unidade.query.filter(Unidade.id.in_(unidades_ids)).all()
            planejamento.unidades.extend(unidades_objs)

        # Adiciona tipos de unidades selecionados
        if tipos_unidade_ids:
            tipos_objs = TipoUnidade.query.filter(TipoUnidade.id.in_(tipos_unidade_ids)).all()
            planejamento.tipos_unidade.extend(tipos_objs)

        for f in request.files.getlist('anexos')[:15]:
            if f and f.filename:
                conteudo = f.read()
                f.seek(0)
                if len(conteudo) / (1024 * 1024) > _MAX_MB:
                    flash(f'O arquivo "{f.filename}" excede o limite de {_MAX_MB} MB.', 'danger')
                    return redirect(url_for('planejamentos.criar'))
                anexo = _salvar_anexo(f, planejamento.id)
                if not anexo:
                    flash(f'O arquivo "{f.filename}" não é permitido.', 'danger')
                    return redirect(url_for('planejamentos.criar'))
                db.session.add(anexo)

        db.session.commit()
        flash('Planejamento criado com sucesso.', 'success')
        return redirect(url_for('planejamentos.listar', expand=planejamento.id, unidade_id=planejamento.unidade_id))

    # Unidade origem: da URL, ou unidade_principal, ou a única unidade do usuário
    unidade_inicial_id = request.args.get('unidade_id', type=int)
    if unidade_inicial_id and unidade_inicial_id not in ids:
        unidade_inicial_id = None
    if unidade_inicial_id is None and getattr(current_user, 'unidade_principal', None):
        up_id = current_user.unidade_principal.id
        if up_id in ids:
            unidade_inicial_id = up_id
    if unidade_inicial_id is None and len(ids) == 1:
        unidade_inicial_id = ids[0]
    if unidade_inicial_id is None and ids:
        unidade_inicial_id = ids[0]
    unidade_origem = Unidade.query.get(unidade_inicial_id) if unidade_inicial_id else None
    # unidades_selecionadas = apenas "outras" unidades (apoio), não a origem
    unidades_selecionadas = []

    return render_template('planejamentos/form_planejamento.html',
        unidades=unidades, tipos_unidade=tipos_unidade, planejamento=None,
        unidade_origem=unidade_origem, unidades_selecionadas=unidades_selecionadas, tipos_selecionados=[],
        ids_unidades_usuario=ids)


@planejamentos_bp.route('/<int:id>')
@planejamentos_bp.route('/<int:id>/kanban')
@login_required
def projeto_detalhe(id):
    """Redireciona para listar com o projeto expandido."""
    planejamento = Planejamento.query.get_or_404(id)
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)
    return redirect(url_for('planejamentos.listar', expand=id, unidade_id=planejamento.unidade_id))


@planejamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_plano_gut'):
        abort(403)

    planejamento = Planejamento.query.get_or_404(id)
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)

    ids = _ids_unidades_usuario()
    from app.models.unidade import Unidade
    from app.models.tipo_unidade import TipoUnidade
    # Para o formulário, mostra todas as unidades ativas (não apenas as vinculadas)
    unidades = Unidade.query.filter(Unidade.status == 'ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        unidade_id = request.form.get('unidade_id', type=int)  # Unidade principal
        # Processa unidades e tipos vindos dos campos hidden (separados por vírgula)
        unidades_ids_str = request.form.get('unidades_ids', '').strip()
        tipos_unidade_ids_str = request.form.get('tipos_unidade_ids', '').strip()
        unidades_ids = [int(x) for x in unidades_ids_str.split(',') if x.strip() and x.strip().isdigit()]
        tipos_unidade_ids = [int(x) for x in tipos_unidade_ids_str.split(',') if x.strip() and x.strip().isdigit()]
        g = request.form.get('gravidade', 1, type=int)
        u = request.form.get('urgencia', 1, type=int)
        t = request.form.get('tendencia', 1, type=int)

        if not titulo:
            flash('Título é obrigatório.', 'danger')
            return redirect(url_for('planejamentos.editar', id=id))

        # Se não selecionou unidades nem tipos, usa a unidade principal
        if not unidades_ids and not tipos_unidade_ids:
            if not unidade_id or unidade_id not in ids:
                flash('Selecione pelo menos uma unidade ou tipo de unidade.', 'danger')
                return redirect(url_for('planejamentos.editar', id=id))
            unidades_ids = [unidade_id]

        # Valida: a unidade origem (primeira) deve ser acessível ao usuário; demais podem ser qualquer unidade (compartilhar)
        if unidades_ids:
            ids_permitidos = set(ids) | {u.id for u in planejamento.unidades.all()} | {planejamento.unidade_id}
            if unidades_ids[0] not in ids_permitidos:
                abort(403)

        planejamento.titulo = titulo
        planejamento.descricao = descricao or None
        planejamento.gravidade = max(1, min(5, g))
        planejamento.urgencia = max(1, min(5, u))
        planejamento.tendencia = max(1, min(5, t))
        # Atualiza unidade principal
        unidade_principal_id = unidades_ids[0] if unidades_ids else unidade_id
        planejamento.unidade_id = unidade_principal_id
        # Salva hora local + 3h para que quando aplicar -3h na exibição, dê o horário correto
        planejamento.atualizado_em = agora_local()
        planejamento.atualizado_por = current_user.id

        # Atualiza unidades vinculadas
        db.session.execute(
            planejamento_unidades.delete().where(
                planejamento_unidades.c.planejamento_id == planejamento.id
            )
        )
        if unidades_ids:
            unidades_objs = Unidade.query.filter(Unidade.id.in_(unidades_ids)).all()
            planejamento.unidades.extend(unidades_objs)

        # Atualiza tipos de unidades vinculados
        db.session.execute(
            planejamento_tipos_unidade.delete().where(
                planejamento_tipos_unidade.c.planejamento_id == planejamento.id
            )
        )
        if tipos_unidade_ids:
            tipos_objs = TipoUnidade.query.filter(TipoUnidade.id.in_(tipos_unidade_ids)).all()
            planejamento.tipos_unidade.extend(tipos_objs)

        for f in request.files.getlist('anexos')[:15]:
            if f and f.filename:
                conteudo = f.read()
                f.seek(0)
                if len(conteudo) / (1024 * 1024) > _MAX_MB:
                    flash(f'O arquivo "{f.filename}" excede o limite de {_MAX_MB} MB.', 'danger')
                    return redirect(url_for('planejamentos.editar', id=id))
                anexo = _salvar_anexo(f, planejamento.id)
                if not anexo:
                    flash(f'O arquivo "{f.filename}" não é permitido.', 'danger')
                    return redirect(url_for('planejamentos.editar', id=id))
                db.session.add(anexo)

        db.session.commit()
        flash('Planejamento atualizado.', 'success')
        return redirect(url_for('planejamentos.listar', expand=planejamento.id, unidade_id=planejamento.unidade_id))

    # Unidade origem e unidades de apoio (exclui a origem da lista de "outras")
    unidade_origem = planejamento.unidade
    unidades_selecionadas = [u.id for u in planejamento.unidades.all() if u.id != planejamento.unidade_id]
    tipos_selecionados = [t.id for t in planejamento.tipos_unidade.all()]
    return render_template('planejamentos/form_planejamento.html', 
                         planejamento=planejamento, 
                         unidades=unidades,
                         tipos_unidade=tipos_unidade,
                         unidade_origem=unidade_origem,
                         unidades_selecionadas=unidades_selecionadas,
                         tipos_selecionados=tipos_selecionados,
                         ids_unidades_usuario=ids)


@planejamentos_bp.route('/<int:plano_id>/acoes/nova', methods=['POST'])
@login_required
def criar_acao(plano_id):
    if not current_user.pode('criar_acao'):
        abort(403)

    planejamento = Planejamento.query.get_or_404(plano_id)
    if not _usuario_pode_editar_planejamento(planejamento):
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

    usuarios_unidade = {u.id for u in _usuarios_planejamento(planejamento)}
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
        planejamento_id=plano_id,
        titulo=titulo,
        descricao=descricao or None,
        status=status,
        ordem=ultima_ordem + 1,
        prazo=prazo,
        criado_por=current_user.id,
    )
    db.session.add(acao)
    db.session.flush()

    planejamento.atualizado_em = agora_local()
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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'ok': True,
            'redirect': url_for('planejamentos.listar', expand=plano_id, unidade_id=planejamento.unidade_id),
        })
    flash('Ação adicionada.', 'success')
    return redirect(url_for('planejamentos.listar', expand=plano_id))


@planejamentos_bp.route('/acoes/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status_acao(id):
    if not current_user.pode('alterar_status_acao'):
        abort(403)

    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)

    status = request.form.get('status', '').strip()
    if status not in STATUS_ACAO:
        return jsonify({'ok': False, 'erro': 'Status inválido'}), 400

    acao.status = status
    agora = agora_local()
    acao.atualizado_em = agora
    acao.atualizado_por = current_user.id
    planejamento.atualizado_em = agora
    planejamento.atualizado_por = current_user.id
    db.session.commit()

    acoes_flat = list(planejamento.acoes.order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id))
    total = len(acoes_flat)
    concluidas = sum(1 for a in acoes_flat if a.status == 'concluido')
    canceladas = sum(1 for a in acoes_flat if a.status == 'cancelado')
    em_andamento = sum(1 for a in acoes_flat if a.status == 'em_andamento')
    pendentes = sum(1 for a in acoes_flat if a.status == 'backlog')
    hoje = hoje_brasilia()
    atrasadas = sum(1 for a in acoes_flat if a.status not in ('concluido', 'cancelado') and a.prazo and a.prazo < hoje)
    total_ativas = total - canceladas
    progresso_pct = round(100 * concluidas / total_ativas) if total_ativas else 0
    em_andamento_pct = round(100 * em_andamento / total_ativas) if total_ativas else 0
    pendentes_pct = round(100 * pendentes / total_ativas) if total_ativas else 0
    
    # Formata data de atualização para retornar ao frontend
    atualizado_br = formatar_brasilia(acao.atualizado_em) if acao.atualizado_em else None
    
    return jsonify({
        'ok': True,
        'status_resumo': {'atrasadas': atrasadas, 'em_andamento': em_andamento, 'pendentes': pendentes, 'concluidas': concluidas, 'canceladas': canceladas},
        'progresso_pct': progresso_pct,
        'em_andamento_pct': em_andamento_pct,
        'pendentes_pct': pendentes_pct,
        'atualizado_em': atualizado_br,
    })


@planejamentos_bp.route('/acoes/<int:id>/responsaveis', methods=['POST'])
@login_required
def atualizar_responsaveis(id):
    if not current_user.pode('criar_acao'):
        abort(403)

    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)

    from app.models.usuario import Usuario
    from app.models.empresa import EmpresaContratada

    responsaveis_ids = request.form.getlist('responsaveis', type=int)
    usuarios_unidade = {u.id for u in _usuarios_planejamento(planejamento)}
    responsaveis_ids = [rid for rid in responsaveis_ids if rid in usuarios_unidade]
    acao.responsaveis = Usuario.query.filter(Usuario.id.in_(responsaveis_ids)).all()

    empresas_ids = request.form.getlist('empresas', type=int)
    empresas_ativas = {e.id for e in EmpresaContratada.query.filter_by(ativo=True).all()}
    empresas_ids = [eid for eid in empresas_ids if eid in empresas_ativas]
    acao.empresas = EmpresaContratada.query.filter(EmpresaContratada.id.in_(empresas_ids)).all()

    # Salva hora local + 3h para que quando aplicar -3h na exibição, dê o horário correto
    acao.atualizado_em = agora_local()
    acao.atualizado_por = current_user.id
    planejamento.atualizado_em = agora_local()
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
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)

    prazo_str = request.form.get('prazo', '').strip()
    prazo_novo = None
    if prazo_str:
        try:
            from datetime import datetime as dt
            prazo_novo = dt.strptime(prazo_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'ok': False, 'erro': 'Data de prazo inválida.'}), 400

    # Regra: ação pode nascer sem prazo e receber um prazo depois,
    # mas, uma vez definido, o prazo não pode mais ser alterado.
    if acao.prazo:
        # Se já existe prazo definido e o novo é diferente, bloqueia alteração
        if not prazo_novo or prazo_novo != acao.prazo:
            return jsonify({
                'ok': False,
                'erro': 'O prazo desta ação já foi definido e não pode ser alterado.'
            }), 400
        # Se for igual, não altera nada, só confirma
    else:
        # Ainda não tinha prazo: permite definir agora (ou continuar sem prazo)
        acao.prazo = prazo_novo
    # Salva hora local + 3h para que quando aplicar -3h na exibição, dê o horário correto
    acao.atualizado_em = agora_local()
    acao.atualizado_por = current_user.id
    planejamento.atualizado_em = agora_local()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    prazo_display = acao.prazo.strftime('%d/%m/%Y') if acao.prazo else ''
    dias_txt = getattr(acao, 'prazo_dias_texto', None) or ''
    return jsonify({
        'ok': True,
        'prazo': prazo_display,
        'prazo_dias_texto': dias_txt,
    })


@planejamentos_bp.route('/acoes/<int:id>/observacoes', methods=['GET'])
@login_required
def listar_observacoes(id):
    """HTML das observações de uma ação — carregado ao expandir (não no GET da lista)."""
    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)
    obs_lista = (
        AcaoObservacao.query.options(
            joinedload(AcaoObservacao.usuario),
            selectinload(AcaoObservacao.anexos),
        )
        .filter_by(acao_id=id)
        .order_by(AcaoObservacao.criado_em.asc())
        .all()
    )
    return render_template(
        'planejamentos/_obs_lista.html',
        acao=acao,
        observacoes=obs_lista,
    )


@planejamentos_bp.route('/acoes/<int:id>/observacao', methods=['POST'])
@login_required
def criar_observacao(id):
    """Adiciona observação em uma ação (HTML + anexos)."""
    acao = AcaoPlanejamento.query.get_or_404(id)
    planejamento = acao.planejamento
    if not _usuario_pode_editar_planejamento(planejamento):
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
        criado_em=agora_local(),
    )
    db.session.add(obs)
    db.session.flush()
    for f in request.files.getlist('anexos')[:10]:
        if f and f.filename:
            conteudo = f.read()
            f.seek(0)
            if len(conteudo) / (1024 * 1024) > _MAX_MB:
                return jsonify({'ok': False, 'erro': f'O arquivo \"{f.filename}\" excede o limite de {_MAX_MB} MB.'}), 413
            anexo = _salvar_obs_anexo(f, obs.id)
            if not anexo:
                return jsonify({'ok': False, 'erro': f'O arquivo \"{f.filename}\" não é permitido.'}), 400
            db.session.add(anexo)
    # Salva hora local + 3h para que quando aplicar -3h na exibição, dê o horário correto
    acao.atualizado_em = agora_local()
    acao.atualizado_por = current_user.id
    planejamento.atualizado_em = agora_local()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    _br_txt = formatar_brasilia(obs.criado_em) if obs.criado_em else ''
    # Garante ordem cronologica (mais antigo primeiro) para anexos
    anexos_ordenados = sorted(list(obs.anexos), key=lambda x: x.id)
    anexos_list = [
        {
            'id': a.id,
            'original': a.original,
            'url': a.url,
            'mime_type': a.mime_type,
            'eh_imagem': a.eh_imagem,
            'eh_audio': a.eh_audio,
            'icone_classe': a.icone_classe
        }
        for a in anexos_ordenados
    ]
    primeiro_nome = ((current_user.nome or '').split() + ['?'])[0]
    return jsonify({
        'ok': True,
        'id': obs.id,
        'texto': obs.texto,
        'criado_em': _br_txt,
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
    if not _usuario_pode_editar_planejamento(planejamento):
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
    planejamento.atualizado_em = agora_local()
    planejamento.atualizado_por = current_user.id
    db.session.commit()
    return jsonify({'ok': True})


@planejamentos_bp.route('/imprimir/projeto/<int:plano_id>')
@login_required
def imprimir_projeto(plano_id):
    """Impressão de um único projeto (ações + observações)."""
    planejamento = Planejamento.query.get_or_404(plano_id)
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)
    acoes_flat = (
        AcaoPlanejamento.query.options(
            selectinload(AcaoPlanejamento.responsaveis),
            selectinload(AcaoPlanejamento.empresas),
            selectinload(AcaoPlanejamento.observacoes).joinedload(AcaoObservacao.usuario),
            selectinload(AcaoPlanejamento.observacoes).selectinload(AcaoObservacao.anexos),
        )
        .filter_by(planejamento_id=plano_id)
        .order_by(AcaoPlanejamento.ordem, AcaoPlanejamento.id)
        .all()
    )
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
        'unidades_do_plano': _unidades_do_planejamento(planejamento),
    }]
    return render_template(
        'planejamentos/imprimir.html',
        planejamentos_dados=planejamentos_dados,
        unidade_filtro=None,
        unidades=[],
        now=agora_local(),
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
    """Página de impressão do planejamento (todos, por unidade e/ou por aba).
    Inclui planos da unidade e planos compartilhados com ela."""
    ids = _ids_unidades_usuario()
    if not ids:
        flash('Você precisa estar vinculado a pelo menos uma unidade.', 'warning')
        return redirect(url_for('planejamentos.listar'))
    aba = request.args.get('aba', 'abertos')
    if aba not in ('abertos', 'concluidos', 'cancelados'):
        aba = 'abertos'
    from app.models.unidade import Unidade
    from app.models.planejamento import planejamento_unidades, planejamento_tipos_unidade

    # IDs de tipos das unidades do usuário
    tipos_unidade_ids = db.session.query(Unidade.tipo_unidade_id).filter(
        Unidade.id.in_(ids),
        Unidade.status == 'ativa',
        Unidade.tipo_unidade_id.isnot(None)
    ).distinct().all()
    tipos_unidade_ids = [t[0] for t in tipos_unidade_ids if t[0]]

    planejamento_ids = set()
    # Planos com unidade_id nas unidades do usuário
    for r in db.session.query(Planejamento.id).filter(Planejamento.unidade_id.in_(ids)).all():
        planejamento_ids.add(r[0])
    # Planos vinculados a unidades específicas
    for r in db.session.query(planejamento_unidades.c.planejamento_id).filter(
        planejamento_unidades.c.unidade_id.in_(ids)
    ).all():
        planejamento_ids.add(r[0])
    # Planos vinculados a tipos que o usuário tem acesso
    if tipos_unidade_ids:
        for r in db.session.query(planejamento_tipos_unidade.c.planejamento_id).filter(
            planejamento_tipos_unidade.c.tipo_unidade_id.in_(tipos_unidade_ids)
        ).all():
            planejamento_ids.add(r[0])

    # Filtro por unidade específica
    if unidade_id and unidade_id in ids:
        planejamento_ids_filtrado = set()
        unidade_obj = Unidade.query.get(unidade_id)
        tipo_unidade_id = unidade_obj.tipo_unidade_id if unidade_obj else None
        for r in db.session.query(Planejamento.id).filter(Planejamento.unidade_id == unidade_id).all():
            planejamento_ids_filtrado.add(r[0])
        for r in db.session.query(planejamento_unidades.c.planejamento_id).filter(
            planejamento_unidades.c.unidade_id == unidade_id
        ).all():
            planejamento_ids_filtrado.add(r[0])
        if tipo_unidade_id:
            for r in db.session.query(planejamento_tipos_unidade.c.planejamento_id).filter(
                planejamento_tipos_unidade.c.tipo_unidade_id == tipo_unidade_id
            ).all():
                planejamento_ids_filtrado.add(r[0])
        planejamento_ids = planejamento_ids_filtrado

    if not planejamento_ids:
        planejamentos = []
    else:
        q = Planejamento.query.options(db.joinedload(Planejamento.unidade)).filter(
            Planejamento.id.in_(planejamento_ids)
        )
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

        # Próxima ação pendente (primeira que não está concluída nem cancelada)
        proxima_acao = None
        for ac in acoes_flat:
            if ac.status not in ('concluido', 'cancelado'):
                proxima_acao = ac
                break

        planejamentos_dados.append({
            'plano': p,
            'acoes_flat': acoes_flat,
            'progresso_pct': progresso_pct,
            'em_andamento_pct': em_andamento_pct,
            'pendentes_pct': pendentes_pct,
            'proxima_acao': proxima_acao,
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
        now=agora_local(),
    )


@planejamentos_bp.route('/obs-anexos/<int:anexo_id>/download')
@login_required
def download_obs_anexo(anexo_id):
    """Download de anexo de observação com nome original."""
    anexo = AcaoObservacaoAnexo.query.get_or_404(anexo_id)
    acao = anexo.observacao.acao
    planejamento = acao.planejamento
    
    # Verifica permissão
    if not _usuario_pode_editar_planejamento(planejamento):
        abort(403)
    
    file_path = os.path.join(_UPLOAD_DIR_OBS, anexo.filename)
    if not os.path.exists(file_path):
        abort(404)
    
    # Força o download com o nome original
    from werkzeug.utils import secure_filename
    return send_file(
        file_path,
        mimetype=anexo.mime_type or 'application/octet-stream',
        as_attachment=True,
        download_name=secure_filename(anexo.original)
    )
