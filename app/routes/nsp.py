# -*- coding: utf-8 -*-
"""Segurança do Paciente — SNI-SGQSP (RI-SGQSP-001).

Qualquer pessoa notifica (com ou sem login, sempre podendo ser anônima). A notificação
vai primeiro ao Núcleo, que qualifica e encaminha às comissões das unidades; a
coordenação da unidade só enxerga o caso quando o Núcleo libera.
"""
import csv
import io
import os
import re
import secrets
import uuid
import mimetypes
from collections import Counter
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
    Response, send_from_directory, jsonify, g,
)
from flask_login import login_required, current_user
from sqlalchemy import func, or_, and_, false
from sqlalchemy.orm import joinedload

from app import db
from app.models.nsp import (
    NspOcorrencia, NspAnexo, NspAndamento, NspEncaminhamento, NspAcao, NspMembro,
    TIPOLOGIAS, TURNOS, FAIXAS_ETARIAS, CLASSIFICACOES, GRAUS_DANO, CRITICIDADES,
    METODOLOGIAS, INV_STATUS, ACAO_STATUS, ETAPAS, ETAPAS_LABEL,
    sugestao_preliminar, eh_nucleo, unidades_comissao, unidades_coordenacao,
)
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.usuario import Usuario
from app.models.notificacao import Notificacao
from app.utils import agora_local, formatar_brasilia, hoje_brasilia, agora_brasilia

nsp_bp = Blueprint('nsp', __name__, url_prefix='/seguranca-paciente')

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'nsp')
_MAX_MB = 10
_HEADER_FILL = PatternFill('solid', fgColor='0D3B5E')
_HEADER_FONT = Font(bold=True, color='FFFFFF')
_HEADER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
_ALFABETO_PROTOCOLO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
_DANOS_COM_DANO = ('Leve', 'Moderado', 'Grave', 'Óbito')


# ══════════════════════════════════════════════════════════
#  PAPÉIS E VISIBILIDADE
# ══════════════════════════════════════════════════════════

def _papeis():
    if 'nsp_papeis' not in g:
        g.nsp_papeis = {
            'nucleo': eh_nucleo(current_user),
            'comissao': unidades_comissao(current_user),
            'coordenacao': unidades_coordenacao(current_user),
        }
    return g.nsp_papeis


def _eh_admin():
    return current_user.is_authenticated and current_user.perfil == 'administrador'


def _pode_gerir_membros():
    return _eh_admin() or _papeis()['nucleo']


def _query_visivel():
    q = NspOcorrencia.query
    p = _papeis()
    if p['nucleo']:
        return q
    conds = []
    if p['comissao']:
        conds.append(NspEncaminhamento.unidade_destino_id.in_(p['comissao']))
    if p['coordenacao']:
        conds.append(and_(
            NspEncaminhamento.unidade_destino_id.in_(p['coordenacao']),
            NspEncaminhamento.liberado_coordenacao.is_(True),
        ))
    if not conds:
        return q.filter(false())
    sub = db.session.query(NspEncaminhamento.ocorrencia_id).filter(or_(*conds))
    return q.filter(NspOcorrencia.id.in_(sub))


def _tem_acesso_painel():
    p = _papeis()
    if p['nucleo'] or p['comissao']:
        return True
    return bool(p['coordenacao']) and _query_visivel().first() is not None


def _papel_caso(o):
    p = _papeis()
    if p['nucleo']:
        return 'nucleo'
    destinos = {e.unidade_destino_id for e in o.encaminhamentos}
    if destinos & p['comissao']:
        return 'comissao'
    liberados = {e.unidade_destino_id for e in o.encaminhamentos if e.liberado_coordenacao}
    if liberados & p['coordenacao']:
        return 'coordenacao'
    return None


def _caso_ou_404(id, *papeis):
    o = NspOcorrencia.query.get_or_404(id)
    papel = _papel_caso(o)
    if not papel:
        abort(404)
    if papeis and papel not in papeis:
        abort(403)
    return o, papel


@nsp_bp.app_context_processor
def _ctx_nsp():
    def nsp_acesso():
        if not current_user.is_authenticated:
            return {'painel': False, 'nucleo': False, 'relatorios': False, 'membros': False}
        p = _papeis()
        return {
            'painel': _tem_acesso_painel(),
            'nucleo': p['nucleo'],
            'relatorios': p['nucleo'] or bool(p['comissao']),
            'membros': _pode_gerir_membros(),
        }
    return {'nsp_acesso': nsp_acesso}


# ══════════════════════════════════════════════════════════
#  AUXILIARES
# ══════════════════════════════════════════════════════════

def _gerar_protocolo():
    ano = hoje_brasilia().year
    while True:
        sufixo = ''.join(secrets.choice(_ALFABETO_PROTOCOLO) for _ in range(6))
        protocolo = f'SP-{ano}-{sufixo}'
        if not NspOcorrencia.query.filter_by(protocolo=protocolo).first():
            return protocolo


def _parse_date(valor):
    valor = (valor or '').strip()
    if not valor:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(valor):
    valor = (valor or '').strip()
    if not valor:
        return None
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M'):
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    return None


def _txt(campo, limite=None):
    v = (request.form.get(campo) or '').strip()
    if limite:
        v = v[:limite]
    return v or None


def _opcao(campo, opcoes):
    v = (request.form.get(campo) or '').strip()
    return v if v in opcoes else None


def _registrar_andamento(o, tipo, texto, anonimo=False):
    db.session.add(NspAndamento(
        ocorrencia_id=o.id,
        tipo=tipo,
        texto=texto,
        criado_por=None if anonimo else current_user.id,
    ))
    o.atualizado_em = agora_local()


def _ids_nucleo():
    rows = db.session.query(NspMembro.usuario_id).join(Usuario, Usuario.id == NspMembro.usuario_id).filter(
        NspMembro.papel == 'nucleo', NspMembro.ativo.is_(True), Usuario.ativo.is_(True)).all()
    return {r[0] for r in rows}


def _ids_comissao(unidade_ids):
    if not unidade_ids:
        return set()
    rows = db.session.query(NspMembro.usuario_id).join(Usuario, Usuario.id == NspMembro.usuario_id).filter(
        NspMembro.papel == 'comissao', NspMembro.ativo.is_(True), Usuario.ativo.is_(True),
        NspMembro.unidade_id.in_(list(unidade_ids))).all()
    return {r[0] for r in rows}


def _ids_coordenacao(unidade_id):
    rows = (
        db.session.query(Usuario.id)
        .join(UsuarioUnidade, UsuarioUnidade.usuario_id == Usuario.id)
        .filter(
            UsuarioUnidade.unidade_id == unidade_id,
            UsuarioUnidade.ativo.is_(True),
            Usuario.ativo.is_(True),
            or_(UsuarioUnidade.papel.in_(['gestor_principal', 'gestor_secundario']),
                Usuario.perfil == 'coordenador'),
        ).all()
    )
    return {r[0] for r in rows}


def _notificar(ids, tipo, titulo, texto, o):
    if current_user.is_authenticated:
        ids = set(ids) - {current_user.id}
    for uid in ids:
        db.session.add(Notificacao(
            usuario_id=uid, tipo=tipo, titulo=titulo[:200], texto=texto, nsp_ocorrencia_id=o.id,
        ))


def _equipe_caso(o):
    """Núcleo e comissões das unidades para onde o caso foi encaminhado."""
    return _ids_nucleo() | _ids_comissao({e.unidade_destino_id for e in o.encaminhamentos})


def _salvar_anexos(o, files):
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    gravados = 0
    for f in files:
        if not f or not getattr(f, 'filename', None):
            continue
        f.stream.seek(0, os.SEEK_END)
        tamanho = f.stream.tell()
        f.stream.seek(0)
        if tamanho > _MAX_MB * 1024 * 1024:
            flash(f'Arquivo "{f.filename}" ultrapassa {_MAX_MB} MB e foi ignorado.', 'warning')
            continue
        original = f.filename
        mime = f.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
        ext = os.path.splitext(original)[1].lower() or ''
        filename = f'{uuid.uuid4().hex}{ext}'
        f.save(os.path.join(_UPLOAD_DIR, filename))
        db.session.add(NspAnexo(
            ocorrencia_id=o.id, filename=filename, original=original,
            mime_type=mime, tamanho_bytes=tamanho, criado_por=current_user.id,
        ))
        gravados += 1
    return gravados


def _voltar(o, aba=None):
    url = url_for('nsp.detalhe', id=o.id)
    return redirect(f'{url}#{aba}' if aba else url)


# ══════════════════════════════════════════════════════════
#  NOTIFICAÇÃO (pública e no SIGUS) — sem vínculo com quem notifica
# ══════════════════════════════════════════════════════════

def _ctx_notificar(form=None, erros=None):
    return dict(
        unidades=Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all(),
        tipologias=TIPOLOGIAS, turnos=TURNOS, faixas=FAIXAS_ETARIAS,
        form=form or {}, erros=erros or [],
        agora=agora_brasilia().strftime('%Y-%m-%dT%H:%M'),
    )


@nsp_bp.route('/notificar', methods=['GET', 'POST'])
def notificar():
    if request.method == 'GET':
        return render_template('nsp/notificar.html', **_ctx_notificar())

    # Honeypot: robôs preenchem o campo invisível.
    if (request.form.get('website') or '').strip():
        return redirect(url_for('nsp.notificar'))

    erros = []
    unidade_id = request.form.get('unidade_id', type=int)
    unidade = Unidade.query.filter_by(id=unidade_id, status='ativa').first() if unidade_id else None
    tipologia = _opcao('tipologia', TIPOLOGIAS)
    turno = _opcao('turno', TURNOS)
    faixa = _opcao('faixa_etaria', FAIXAS_ETARIAS)
    local = _txt('local_incidente', 150)
    ocorrencia_em = _parse_datetime(request.form.get('ocorrencia_em'))
    identificacao_em = _parse_datetime(request.form.get('identificacao_em'))
    codigo = _txt('paciente_codigo', 60)
    descricao = _txt('descricao')
    agora = agora_brasilia()

    if not unidade:
        erros.append('Selecione a unidade notificante.')
    if not tipologia:
        erros.append('Selecione a tipologia do serviço.')
    if not local:
        erros.append('Informe o setor/local do incidente.')
    if not turno:
        erros.append('Selecione o turno.')
    if not ocorrencia_em:
        erros.append('Informe a data e a hora da ocorrência.')
    elif ocorrencia_em > agora:
        erros.append('A data da ocorrência não pode estar no futuro.')
    if not identificacao_em:
        erros.append('Informe a data e a hora da identificação.')
    elif ocorrencia_em and identificacao_em < ocorrencia_em:
        erros.append('A identificação não pode ser anterior à ocorrência.')
    if not codigo:
        erros.append('Informe o identificador codificado do paciente.')
    elif re.fullmatch(r'[\d.\-/ ]{11,}', codigo):
        erros.append('O identificador parece um CPF, CNS ou prontuário. Use um código que não identifique o paciente.')
    if not faixa:
        erros.append('Selecione a faixa etária.')
    if not descricao:
        erros.append('Descreva o ocorrido.')

    if erros:
        return render_template('nsp/notificar.html', **_ctx_notificar(request.form, erros))

    nome = _txt('notificante_nome', 150)
    o = NspOcorrencia(
        protocolo=_gerar_protocolo(),
        unidade_id=unidade.id,
        etapa='em_qualificacao',
        origem='sigus' if current_user.is_authenticated else 'publico',
        anonimo=not nome,
        tipologia=tipologia,
        local_incidente=local,
        turno=turno,
        ocorrencia_em=ocorrencia_em,
        identificacao_em=identificacao_em,
        data_ocorrencia=ocorrencia_em.date(),
        hora_ocorrencia=ocorrencia_em.time(),
        paciente_codigo=codigo,
        faixa_etaria=faixa,
        descricao=descricao,
        acao_imediata=_txt('acao_imediata'),
        notificante_nome=nome,
        notificante_cargo=_txt('notificante_cargo', 120),
        criado_por=None,
    )
    db.session.add(o)
    db.session.flush()
    _registrar_andamento(o, 'registro', 'Notificação recebida pelo Núcleo de Segurança do Paciente.', anonimo=True)
    _notificar(
        _ids_nucleo(), 'nsp_novo',
        f'Nova notificação {o.protocolo}',
        f'{tipologia} · {unidade.nome}. Aguardando qualificação.', o,
    )
    db.session.commit()
    return redirect(url_for('nsp.notificado', protocolo=o.protocolo))


@nsp_bp.route('/notificado/<protocolo>')
def notificado(protocolo):
    o = NspOcorrencia.query.filter_by(protocolo=protocolo.upper()).first_or_404()
    return render_template('nsp/notificado.html', protocolo=o.protocolo)


@nsp_bp.route('/acompanhar')
def acompanhar():
    protocolo = (request.args.get('protocolo') or '').strip().upper()
    o = None
    if protocolo:
        o = NspOcorrencia.query.filter(func.upper(NspOcorrencia.protocolo) == protocolo).first()
    return render_template('nsp/acompanhar.html', protocolo=protocolo, o=o, buscou=bool(protocolo))


# ══════════════════════════════════════════════════════════
#  PAINEL DO NÚCLEO / COMISSÕES
# ══════════════════════════════════════════════════════════

def _filtrar(q):
    args = request.args
    etapas = [e for e in args.getlist('etapa') if e in ETAPAS_LABEL]
    criticidades = [c for c in args.getlist('criticidade') if c in CRITICIDADES]
    tipologias = [t for t in args.getlist('tipologia') if t in TIPOLOGIAS]
    classificacoes = [c for c in args.getlist('classificacao') if c in CLASSIFICACOES]
    unidade_ids = args.getlist('unidade', type=int)
    busca = (args.get('q') or '').strip()
    de = _parse_date(args.get('de'))
    ate = _parse_date(args.get('ate'))
    data_ref = func.coalesce(NspOcorrencia.ocorrencia_em, NspOcorrencia.criado_em)

    if etapas:
        q = q.filter(NspOcorrencia.etapa.in_(etapas))
    if criticidades:
        q = q.filter(NspOcorrencia.qual_criticidade.in_(criticidades))
    if tipologias:
        q = q.filter(NspOcorrencia.tipologia.in_(tipologias))
    if classificacoes:
        q = q.filter(NspOcorrencia.qual_classificacao.in_(classificacoes))
    if unidade_ids:
        q = q.filter(NspOcorrencia.unidade_id.in_(unidade_ids))
    if busca:
        like = f'%{busca}%'
        q = q.filter(or_(
            NspOcorrencia.protocolo.ilike(like),
            NspOcorrencia.descricao.ilike(like),
            NspOcorrencia.local_incidente.ilike(like),
            NspOcorrencia.paciente_codigo.ilike(like),
        ))
    if de:
        q = q.filter(func.date(data_ref) >= de)
    if ate:
        q = q.filter(func.date(data_ref) <= ate)
    return q


def _opcoes_filtro():
    return dict(
        unidades=Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all(),
        etapas_opts={s: l for s, l, _ in ETAPAS},
        criticidades_opts={c: c for c in CRITICIDADES},
        tipologias_opts={t: t for t in TIPOLOGIAS},
        classificacoes_opts={c: c for c in CLASSIFICACOES},
        filtros=request.args,
    )


@nsp_bp.route('/')
@login_required
def index():
    if not _tem_acesso_painel():
        return render_template('nsp/inicio.html', pode_membros=_pode_gerir_membros())

    base = _query_visivel()
    todos = base.options(joinedload(NspOcorrencia.acoes)).all()
    kpis = {
        'total': len(todos),
        'pendentes': sum(1 for o in todos if o.etapa == 'em_qualificacao'),
        'investigacao': sum(1 for o in todos if o.etapa == 'em_investigacao'),
        'plano': sum(1 for o in todos if o.acoes and not o.encerrada),
        'alta': sum(1 for o in todos if o.qual_criticidade in ('Alta', 'Crítica')),
    }
    ocorrencias = (
        _filtrar(base)
        .options(joinedload(NspOcorrencia.unidade),
                 joinedload(NspOcorrencia.encaminhamentos).joinedload(NspEncaminhamento.unidade_destino))
        .order_by(NspOcorrencia.criado_em.desc())
        .limit(500).all()
    )
    return render_template(
        'nsp/index.html', ocorrencias=ocorrencias, kpis=kpis, papeis=_papeis(), **_opcoes_filtro(),
    )


# ══════════════════════════════════════════════════════════
#  DETALHE
# ══════════════════════════════════════════════════════════

@nsp_bp.route('/<int:id>')
@login_required
def detalhe(id):
    o, papel = _caso_ou_404(id)
    from app.sis_consulta import configurado as sis_configurado
    ja_encaminhadas = {e.unidade_destino_id for e in o.encaminhamentos}
    return render_template(
        'nsp/detalhe.html',
        o=o, papel=papel,
        sugestao=sugestao_preliminar(o.descricao, o.acao_imediata),
        unidades=Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all(),
        ja_encaminhadas=ja_encaminhadas,
        classificacoes=CLASSIFICACOES, danos=GRAUS_DANO, criticidades=CRITICIDADES,
        metodologias=METODOLOGIAS, inv_status_opts=INV_STATUS, acao_status_opts=ACAO_STATUS,
        sis_ok=sis_configurado(),
        hoje=hoje_brasilia(),
    )


@nsp_bp.route('/<int:id>/imprimir')
@login_required
def imprimir(id):
    o, papel = _caso_ou_404(id)
    return render_template('nsp/imprimir.html', o=o, papel=papel, now=agora_local())


@nsp_bp.route('/<int:id>/qualificar', methods=['POST'])
@login_required
def qualificar(id):
    o, _ = _caso_ou_404(id, 'nucleo')
    if o.encerrada:
        flash('Notificação encerrada. Reabra para alterar.', 'warning')
        return _voltar(o, 'qualificacao')
    classificacao = _opcao('qual_classificacao', CLASSIFICACOES)
    dano = _opcao('qual_dano', GRAUS_DANO)
    criticidade = _opcao('qual_criticidade', CRITICIDADES)
    if not (classificacao and dano and criticidade):
        flash('Informe classificação, grau de dano e criticidade.', 'danger')
        return _voltar(o, 'qualificacao')
    o.qual_classificacao = classificacao
    o.qual_dano = dano
    o.qual_criticidade = criticidade
    o.qual_diagnostico = _txt('qual_diagnostico')
    o.qual_fundamentacao = _txt('qual_fundamentacao')
    o.never_event = request.form.get('never_event') == '1'
    o.qualificado_por = current_user.id
    o.qualificado_em = agora_local()
    if o.etapa == 'em_qualificacao':
        o.etapa = 'qualificada'
    _registrar_andamento(o, 'analise', f'Qualificação: {classificacao} · dano {dano} · criticidade {criticidade}.')
    db.session.commit()
    flash('Qualificação salva.', 'success')
    return _voltar(o, 'qualificacao')


@nsp_bp.route('/<int:id>/encaminhar', methods=['POST'])
@login_required
def encaminhar(id):
    o, _ = _caso_ou_404(id, 'nucleo')
    if o.encerrada:
        flash('Notificação encerrada.', 'warning')
        return _voltar(o, 'encaminhamento')
    if not o.qual_classificacao:
        flash('Qualifique a notificação antes de encaminhar às comissões.', 'warning')
        return _voltar(o, 'qualificacao')
    ja = {e.unidade_destino_id for e in o.encaminhamentos}
    ids = {i for i in request.form.getlist('unidade_ids', type=int) if i not in ja}
    unidades = Unidade.query.filter(Unidade.id.in_(ids)).all() if ids else []
    if not unidades:
        flash('Escolha ao menos uma unidade que ainda não recebeu o caso.', 'danger')
        return _voltar(o, 'encaminhamento')
    texto = _txt('texto')
    for u in unidades:
        db.session.add(NspEncaminhamento(
            ocorrencia_id=o.id,
            destino_outro='Comissão de Segurança do Paciente',
            unidade_destino_id=u.id,
            texto=texto,
            criado_por=current_user.id,
        ))
    if o.etapa in ('em_qualificacao', 'qualificada'):
        o.etapa = 'encaminhada'
    nomes = ', '.join(u.nome for u in unidades)
    _registrar_andamento(o, 'encaminhamento', f'Encaminhada à comissão de: {nomes}. {texto or ""}'.strip())
    _notificar(
        _ids_comissao({u.id for u in unidades}), 'nsp_encaminhado',
        f'{o.protocolo} encaminhada à comissão',
        f'O Núcleo encaminhou um caso para investigação na sua unidade. {texto or ""}'.strip(), o,
    )
    db.session.commit()
    flash(f'Encaminhada para {nomes}.', 'success')
    return _voltar(o, 'encaminhamento')


@nsp_bp.route('/<int:id>/encaminhamento/<int:enc_id>/coordenacao', methods=['POST'])
@login_required
def liberar_coordenacao(id, enc_id):
    o, _ = _caso_ou_404(id, 'nucleo')
    enc = NspEncaminhamento.query.filter_by(id=enc_id, ocorrencia_id=o.id).first_or_404()
    liberar = request.form.get('liberar') == '1'
    for e in o.encaminhamentos:
        if e.unidade_destino_id == enc.unidade_destino_id:
            e.liberado_coordenacao = liberar
            e.liberado_por = current_user.id if liberar else None
            e.liberado_em = agora_local() if liberar else None
    un = enc.unidade_destino.nome if enc.unidade_destino else '—'
    if liberar:
        _registrar_andamento(o, 'encaminhamento', f'Acesso liberado à coordenação de {un}.')
        _notificar(
            _ids_coordenacao(enc.unidade_destino_id), 'nsp_encaminhado',
            f'{o.protocolo} liberada para a coordenação',
            'O Núcleo de Segurança do Paciente compartilhou um caso com a coordenação da unidade.', o,
        )
    else:
        _registrar_andamento(o, 'encaminhamento', f'Acesso da coordenação de {un} revogado.')
    db.session.commit()
    flash('Acesso da coordenação ' + ('liberado.' if liberar else 'revogado.'), 'success')
    return _voltar(o, 'encaminhamento')


@nsp_bp.route('/<int:id>/investigacao', methods=['POST'])
@login_required
def investigacao(id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    if o.encerrada:
        flash('Notificação encerrada.', 'warning')
        return _voltar(o, 'investigacao')
    o.inv_metodologia = _opcao('inv_metodologia', METODOLOGIAS)
    o.inv_status = _opcao('inv_status', INV_STATUS) or 'Não iniciada'
    o.fatores_contribuintes = _txt('fatores_contribuintes')
    o.inv_barreiras = _txt('inv_barreiras')
    o.inv_causas = _txt('inv_causas')
    o.inv_conclusao = _txt('inv_conclusao')
    o.inv_por = current_user.id
    o.inv_em = agora_local()
    if o.inv_status != 'Não iniciada' and o.etapa in ('qualificada', 'encaminhada'):
        o.etapa = 'em_investigacao'
    _registrar_andamento(o, 'analise', f'Investigação atualizada ({o.inv_status}'
                         + (f' · {o.inv_metodologia}' if o.inv_metodologia else '') + ').')
    _notificar(_equipe_caso(o), 'nsp_andamento', f'Investigação em {o.protocolo}',
               f'Status da investigação: {o.inv_status}.', o)
    db.session.commit()
    flash('Investigação salva.', 'success')
    return _voltar(o, 'investigacao')


@nsp_bp.route('/<int:id>/acao', methods=['POST'])
@login_required
def nova_acao(id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    if o.encerrada:
        flash('Notificação encerrada.', 'warning')
        return _voltar(o, 'plano')
    descricao = _txt('descricao')
    if not descricao:
        flash('Descreva a ação.', 'danger')
        return _voltar(o, 'plano')
    db.session.add(NspAcao(
        ocorrencia_id=o.id,
        descricao=descricao,
        responsavel_nome=_txt('responsavel_nome', 150),
        prazo=_parse_date(request.form.get('prazo')),
        indicador=_txt('indicador', 255),
        status='Aberta',
        criado_por=current_user.id,
    ))
    _registrar_andamento(o, 'acao', f'Ação incluída no plano: {descricao[:180]}')
    _notificar(_equipe_caso(o), 'nsp_andamento', f'Plano de ação em {o.protocolo}', descricao[:180], o)
    db.session.commit()
    flash('Ação incluída no plano.', 'success')
    return _voltar(o, 'plano')


@nsp_bp.route('/<int:id>/acao/<int:acao_id>/status', methods=['POST'])
@login_required
def status_acao(id, acao_id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    acao = NspAcao.query.filter_by(id=acao_id, ocorrencia_id=o.id).first_or_404()
    status = _opcao('status', ACAO_STATUS)
    if status and status != acao.status_label:
        acao.status = status
        acao.concluida = status == 'Concluída'
        acao.concluida_em = agora_local() if acao.concluida else None
        _registrar_andamento(o, 'acao', f'Ação "{acao.descricao[:120]}" agora está {status.lower()}.')
        db.session.commit()
    return _voltar(o, 'plano')


@nsp_bp.route('/<int:id>/acao/<int:acao_id>/excluir', methods=['POST'])
@login_required
def excluir_acao(id, acao_id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    acao = NspAcao.query.filter_by(id=acao_id, ocorrencia_id=o.id).first_or_404()
    _registrar_andamento(o, 'acao', f'Ação removida do plano: {acao.descricao[:160]}')
    db.session.delete(acao)
    db.session.commit()
    flash('Ação removida.', 'success')
    return _voltar(o, 'plano')


@nsp_bp.route('/<int:id>/etapa', methods=['POST'])
@login_required
def mudar_etapa(id):
    o, _ = _caso_ou_404(id, 'nucleo')
    acao = request.form.get('acao')
    motivo = _txt('motivo')
    if acao == 'concluir':
        if not o.qual_classificacao:
            flash('Qualifique a notificação antes de concluir.', 'danger')
            return _voltar(o, 'qualificacao')
        if o.exige_investigacao and not o.investigacao_preenchida:
            flash('Evento sentinela, dano grave/óbito, criticidade crítica ou evento que nunca deveria ocorrer '
                  'exigem investigação concluída (com conclusão) antes de encerrar.', 'danger')
            return _voltar(o, 'investigacao')
        o.etapa = 'concluida'
        o.encerrado_em = agora_local()
        _registrar_andamento(o, 'status', 'Notificação concluída pelo Núcleo.' + (f' {motivo}' if motivo else ''))
    elif acao == 'arquivar':
        if not motivo:
            flash('Informe o motivo do arquivamento.', 'danger')
            return _voltar(o)
        o.etapa = 'arquivada'
        o.encerrado_em = agora_local()
        _registrar_andamento(o, 'status', f'Notificação arquivada pelo Núcleo. Motivo: {motivo}')
    elif acao == 'reabrir':
        if o.inv_status and o.inv_status != 'Não iniciada':
            o.etapa = 'em_investigacao'
        elif o.encaminhamentos:
            o.etapa = 'encaminhada'
        elif o.qual_classificacao:
            o.etapa = 'qualificada'
        else:
            o.etapa = 'em_qualificacao'
        o.encerrado_em = None
        _registrar_andamento(o, 'status', 'Notificação reaberta pelo Núcleo.' + (f' {motivo}' if motivo else ''))
    else:
        abort(400)
    _notificar(_equipe_caso(o), 'nsp_andamento', f'{o.protocolo}: {o.etapa_label}', motivo or o.etapa_label, o)
    db.session.commit()
    flash(f'Etapa: {o.etapa_label}.', 'success')
    return _voltar(o)


@nsp_bp.route('/<int:id>/paciente', methods=['POST'])
@login_required
def paciente(id):
    o, _ = _caso_ou_404(id, 'nucleo')
    o.nome_afetado = _txt('nome_afetado', 150)
    o.data_nascimento = _parse_date(request.form.get('data_nascimento'))
    o.prontuario = _txt('prontuario', 40)
    o.cpf = re.sub(r'\D+', '', request.form.get('cpf') or '') or None
    o.cns = re.sub(r'\D+', '', request.form.get('cns') or '') or None
    _registrar_andamento(o, 'analise', 'Dados de identificação do paciente atualizados pelo Núcleo.')
    db.session.commit()
    flash('Dados do paciente salvos.', 'success')
    return _voltar(o, 'paciente')


@nsp_bp.route('/buscar-sis', methods=['POST'])
@login_required
def buscar_sis():
    if not _papeis()['nucleo']:
        abort(403)
    from app.sis_consulta import buscar_paciente
    payload = request.get_json(silent=True) or {}
    termo = (request.form.get('q') or payload.get('q') or '').strip()
    tipo = (request.form.get('tipo') or payload.get('tipo') or '').strip().lower()
    if not termo:
        return jsonify(ok=False, erro='Informe o CPF, o CNS ou o prontuário.'), 400
    try:
        return jsonify(buscar_paciente(termo, tipo=tipo or None))
    except ValueError as exc:
        return jsonify(ok=False, erro=str(exc)), 400
    except Exception as exc:
        return jsonify(ok=False, erro=str(exc) or 'Não foi possível consultar o SIS.'), 502


@nsp_bp.route('/<int:id>/comentario', methods=['POST'])
@login_required
def comentario(id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    texto = _txt('texto')
    if not texto:
        flash('Escreva o comentário.', 'danger')
        return _voltar(o, 'historico')
    _registrar_andamento(o, 'comentario', texto)
    _notificar(_equipe_caso(o), 'nsp_andamento', f'Comentário em {o.protocolo}', texto[:180], o)
    db.session.commit()
    flash('Comentário registrado.', 'success')
    return _voltar(o, 'historico')


@nsp_bp.route('/<int:id>/anexos', methods=['POST'])
@login_required
def anexar(id):
    o, _ = _caso_ou_404(id, 'nucleo', 'comissao')
    n = _salvar_anexos(o, request.files.getlist('anexos'))
    if n:
        _registrar_andamento(o, 'anexo', f'{n} arquivo(s) anexado(s).')
        db.session.commit()
        flash(f'{n} arquivo(s) anexado(s).', 'success')
    else:
        flash(f'Nenhum arquivo válido enviado (limite {_MAX_MB} MB).', 'warning')
    return _voltar(o, 'anexos')


@nsp_bp.route('/anexo/<int:id>/baixar')
@login_required
def baixar_anexo(id):
    anexo = NspAnexo.query.get_or_404(id)
    _caso_ou_404(anexo.ocorrencia_id, 'nucleo', 'comissao')
    return send_from_directory(_UPLOAD_DIR, anexo.filename, as_attachment=True,
                               download_name=anexo.original or anexo.filename)


# ══════════════════════════════════════════════════════════
#  RELATÓRIOS + DASHBOARD
# ══════════════════════════════════════════════════════════

def _exigir_relatorios():
    p = _papeis()
    if not (p['nucleo'] or p['comissao']):
        abort(403)


def _com_dano(o):
    return o.qual_dano in _DANOS_COM_DANO or o.qual_classificacao == 'Incidente com dano / evento adverso'


def _distribuicao(contador, ordem=None, limite=None):
    total = sum(contador.values()) or 1
    if ordem:
        itens = [(k, contador.get(k, 0)) for k in ordem if contador.get(k, 0)]
        itens += [(k, v) for k, v in contador.items() if k not in ordem]
    else:
        itens = contador.most_common(limite)
    maior = max((v for _, v in itens), default=1) or 1
    return [{'label': k, 'n': v, 'pct': round(v * 100 / total), 'w': round(v * 100 / maior)} for k, v in itens]


@nsp_bp.route('/relatorios')
@login_required
def relatorios():
    _exigir_relatorios()
    ocorrencias = (
        _filtrar(_query_visivel())
        .options(joinedload(NspOcorrencia.unidade), joinedload(NspOcorrencia.acoes),
                 joinedload(NspOcorrencia.encaminhamentos))
        .order_by(NspOcorrencia.criado_em.desc()).all()
    )
    acoes = [a for o in ocorrencias for a in o.acoes]
    tempos = [
        max(0.0, (o.qualificado_em - o.criado_em).total_seconds() / 86400)
        for o in ocorrencias if o.qualificado_em and o.criado_em
    ]
    kpis = {
        'total': len(ocorrencias),
        'pendentes': sum(1 for o in ocorrencias if o.etapa == 'em_qualificacao'),
        'com_dano': sum(1 for o in ocorrencias if _com_dano(o)),
        'alta': sum(1 for o in ocorrencias if o.qual_criticidade in ('Alta', 'Crítica')),
        'concluidas': sum(1 for o in ocorrencias if o.etapa == 'concluida'),
        'acoes': len(acoes),
        'acoes_vencidas': sum(1 for a in acoes if a.vencida),
        'anonimas': sum(1 for o in ocorrencias if o.anonimo),
        'tempo_qualificacao': round(sum(tempos) / len(tempos), 1) if tempos else None,
    }

    por_mes = Counter()
    for o in ocorrencias:
        ref = o.ocorrencia_em or o.criado_em
        if ref:
            por_mes[ref.strftime('%Y-%m')] += 1
    meses = sorted(por_mes)[-12:]

    def contar(attr, vazio='Não informado'):
        return Counter((getattr(o, attr) or vazio) for o in ocorrencias)

    graficos = [
        ('Por tipologia', _distribuicao(contar('tipologia'), TIPOLOGIAS)),
        ('Por classificação', _distribuicao(contar('qual_classificacao', 'Aguardando qualificação'), CLASSIFICACOES)),
        ('Por grau de dano', _distribuicao(contar('qual_dano', 'Aguardando qualificação'), GRAUS_DANO)),
        ('Por criticidade', _distribuicao(contar('qual_criticidade', 'Aguardando qualificação'), CRITICIDADES)),
        ('Por etapa', _distribuicao(Counter(o.etapa_label for o in ocorrencias), [l for _, l, _ in ETAPAS])),
        ('Por turno', _distribuicao(contar('turno'), TURNOS)),
        ('Por faixa etária', _distribuicao(contar('faixa_etaria'), FAIXAS_ETARIAS)),
        ('Por metodologia de investigação', _distribuicao(Counter(o.inv_metodologia for o in ocorrencias if o.inv_metodologia), METODOLOGIAS)),
        ('Status do plano de ação', _distribuicao(Counter('Vencida' if a.vencida else a.status_label for a in acoes), ACAO_STATUS + ['Vencida'])),
        ('Unidades notificantes (top 15)', _distribuicao(Counter(o.unidade.nome if o.unidade else '—' for o in ocorrencias), limite=15)),
    ]
    return render_template(
        'nsp/relatorios.html',
        ocorrencias=ocorrencias, kpis=kpis, graficos=graficos,
        por_mes=_distribuicao(Counter({m: por_mes[m] for m in meses}), meses),
        **_opcoes_filtro(),
    )


def _linhas_exportacao(ocorrencias):
    cab = [
        'Protocolo', 'Recebida em', 'Origem', 'Unidade notificante', 'Tipologia', 'Setor/local', 'Turno',
        'Ocorrência', 'Identificação', 'Identificador do paciente', 'Faixa etária',
        'Descrição', 'Ações imediatas', 'Notificante identificado', 'Etapa',
        'Classificação', 'Grau de dano', 'Criticidade', 'Nunca deveria ocorrer', 'Diagnóstico',
        'Unidades encaminhadas', 'Investigação', 'Metodologia', 'Conclusão da investigação',
        'Ações (total)', 'Ações concluídas', 'Ações vencidas', 'Encerrada em',
    ]
    linhas = [cab]
    for o in ocorrencias:
        linhas.append([
            o.protocolo,
            formatar_brasilia(o.criado_em) if o.criado_em else '',
            'Link público' if o.origem == 'publico' else 'SIGUS',
            o.unidade.nome if o.unidade else '',
            o.tipologia or '',
            o.local_incidente or '',
            o.turno or '',
            o.ocorrencia_em.strftime('%d/%m/%Y %H:%M') if o.ocorrencia_em else (
                o.data_ocorrencia.strftime('%d/%m/%Y') if o.data_ocorrencia else ''),
            o.identificacao_em.strftime('%d/%m/%Y %H:%M') if o.identificacao_em else '',
            o.paciente_codigo or '',
            o.faixa_etaria or '',
            (o.descricao or '').replace('\n', ' '),
            (o.acao_imediata or '').replace('\n', ' '),
            'Não' if o.anonimo else 'Sim',
            o.etapa_label,
            o.qual_classificacao or '',
            o.qual_dano or '',
            o.qual_criticidade or '',
            'Sim' if o.never_event else 'Não',
            (o.qual_diagnostico or '').replace('\n', ' '),
            ', '.join(e.unidade_destino.nome for e in o.unidades_encaminhadas if e.unidade_destino),
            o.inv_status or '',
            o.inv_metodologia or '',
            (o.inv_conclusao or '').replace('\n', ' '),
            len(o.acoes),
            sum(1 for a in o.acoes if a.status_label == 'Concluída'),
            len(o.acoes_vencidas),
            formatar_brasilia(o.encerrado_em) if o.encerrado_em else '',
        ])
    return linhas


@nsp_bp.route('/relatorios/exportar/<formato>')
@login_required
def exportar(formato):
    _exigir_relatorios()
    ocorrencias = (
        _filtrar(_query_visivel())
        .options(joinedload(NspOcorrencia.unidade), joinedload(NspOcorrencia.acoes))
        .order_by(NspOcorrencia.criado_em.desc()).all()
    )
    linhas = _linhas_exportacao(ocorrencias)
    nome = f'seguranca_paciente_{agora_brasilia().strftime("%Y%m%d_%H%M")}'

    if formato == 'csv':
        buf = io.StringIO()
        csv.writer(buf, delimiter=';').writerows(linhas)
        return Response(
            '\ufeff' + buf.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="{nome}.csv"'},
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Notificações'
    ws.append(linhas[0])
    for cell in ws[1]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _HEADER_ALIGN
    for linha in linhas[1:]:
        ws.append(linha)
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(42, max(12, len(str(col[0].value or '')) + 4))
    out = io.BytesIO()
    wb.save(out)
    return Response(
        out.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{nome}.xlsx"'},
    )


# ══════════════════════════════════════════════════════════
#  MEMBROS — Núcleo e comissões das unidades
# ══════════════════════════════════════════════════════════

@nsp_bp.route('/membros', methods=['GET', 'POST'])
@login_required
def membros():
    if not _pode_gerir_membros():
        abort(403)
    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'adicionar':
            papel = request.form.get('papel')
            usuario_id = request.form.get('usuario_id', type=int)
            unidade_id = request.form.get('unidade_id', type=int) if papel == 'comissao' else None
            usuario = Usuario.query.filter_by(id=usuario_id, ativo=True).first() if usuario_id else None
            if papel not in NspMembro.PAPEIS or not usuario or (papel == 'comissao' and not unidade_id):
                flash('Escolha o usuário' + (' e a unidade.' if papel == 'comissao' else '.'), 'danger')
            elif papel == 'nucleo' and not (_eh_admin() or _papeis()['nucleo']):
                abort(403)
            else:
                existente = NspMembro.query.filter_by(usuario_id=usuario.id, papel=papel, unidade_id=unidade_id).first()
                if existente:
                    existente.ativo = True
                else:
                    db.session.add(NspMembro(usuario_id=usuario.id, papel=papel, unidade_id=unidade_id,
                                             criado_por=current_user.id))
                db.session.commit()
                flash(f'{usuario.nome} incluído(a).', 'success')
        elif acao == 'remover':
            m = NspMembro.query.get_or_404(request.form.get('membro_id', type=int))
            if m.papel == 'nucleo' and m.usuario_id == current_user.id and not _eh_admin():
                flash('Você não pode remover a si mesmo do Núcleo.', 'warning')
            else:
                db.session.delete(m)
                db.session.commit()
                flash('Membro removido.', 'success')
        return redirect(url_for('nsp.membros', aba=request.form.get('papel') or request.args.get('aba')))

    todos = (NspMembro.query.filter_by(ativo=True)
             .options(joinedload(NspMembro.usuario), joinedload(NspMembro.unidade)).all())
    nucleo = sorted((m for m in todos if m.papel == 'nucleo'), key=lambda m: m.usuario.nome.lower())
    comissoes = {}
    for m in todos:
        if m.papel == 'comissao' and m.unidade:
            comissoes.setdefault(m.unidade, []).append(m)
    comissoes = sorted(
        ((u, sorted(ms, key=lambda m: m.usuario.nome.lower())) for u, ms in comissoes.items()),
        key=lambda x: x[0].nome,
    )
    return render_template(
        'nsp/membros.html',
        nucleo=nucleo, comissoes=comissoes,
        usuarios=Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all(),
        unidades=Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all(),
        aba=request.args.get('aba') or 'nucleo',
    )
