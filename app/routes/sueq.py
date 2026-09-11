# -*- coding: utf-8 -*-
"""Módulos SUEQ convertidos do dashboard-emendas (Patrick) para o SIGUS."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models.sueq import (
    SueqChamado, SueqChamadoControle, SueqEmenda, SueqEmendaItem,
    SueqParlamentar, SueqProcesso, SueqUnidade,
)
from app.models.unidade import Unidade

sueq_bp = Blueprint('sueq', __name__, url_prefix='/sueq')

TIPOS_EMENDA = ['MUNICIPAL', 'ESTADUAL', 'FEDERAL', 'Municipal', 'Estadual', 'Federal']
STATUS_ITEM = ['Aguardando licitação', 'Em licitação', 'Entregue', 'Cancelado']
STATUS_PROCESSO = ['Em andamento', 'Homologado', 'Fracassado', 'Deserto', 'Revogado']
MODALIDADES = [
    'Pregão Eletrônico', 'Pregão Presencial', 'Dispensa de Licitação',
    'Inexigibilidade', 'Concorrência', 'Tomada de Preços',
]
URGENCIAS = ['Baixa', 'Média', 'Alta']
STATUS_CHAMADO = [
    'Aguardando abertura', 'Aberto', 'Em atendimento',
    'Aguardando peça', 'Encerrado', 'Inválido',
]


def _exige(*acoes):
    if not any(current_user.pode(a) for a in acoes):
        abort(403)


def _decimal(val):
    if val in (None, ''):
        return None
    s = str(val).strip()
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _proximo_protocolo():
    ano = datetime.now().year
    prefixo = f'SUEQ-{ano}-'
    existentes = [
        c.protocolo for c in SueqChamado.query.filter(SueqChamado.protocolo.like(f'{prefixo}%')).all()
        if c.protocolo
    ]
    nums = []
    for p in existentes:
        try:
            nums.append(int(p.rsplit('-', 1)[-1]))
        except ValueError:
            pass
    nxt = (max(nums) + 1) if nums else 1
    return f'{prefixo}{nxt:04d}'


# ── Emendas ──────────────────────────────────────────────────────────────────

@sueq_bp.route('/emendas')
@login_required
def emendas():
    _exige('ver_emendas', 'editar_emendas', 'adicionar_emendas')
    q = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '')
    query = SueqEmenda.query.order_by(SueqEmenda.ano.desc(), SueqEmenda.emenda.desc())
    if tipo:
        query = query.filter(SueqEmenda.tipo == tipo)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            SueqEmenda.emenda.ilike(like),
            SueqEmenda.parlamentar.ilike(like),
            SueqEmenda.unidade.ilike(like),
            SueqEmenda.sei_emenda.ilike(like),
        ))
    lista = query.all()
    kpis = {
        'qtd': len(lista),
        'cedido': sum((e.valor_cedido or 0) for e in lista),
        'executado': sum((e.total_executado or 0) for e in lista),
        'itens': sum(e.itens.count() for e in lista),
    }
    return render_template(
        'sueq/emendas_listar.html', lista=lista, kpis=kpis,
        filtro_q=q, filtro_tipo=tipo, tipos=TIPOS_EMENDA,
    )


@sueq_bp.route('/emendas/nova', methods=['GET', 'POST'])
@login_required
def emenda_nova():
    _exige('adicionar_emendas')
    unidades = SueqUnidade.query.filter_by(ativo=True).order_by(SueqUnidade.nome).all()
    parlamentares = SueqParlamentar.query.filter_by(ativo=True).order_by(SueqParlamentar.nome).all()
    if request.method == 'POST':
        uid = request.form.get('unidade_id', type=int)
        unid = SueqUnidade.query.get(uid) if uid else None
        e = SueqEmenda(
            tipo=request.form.get('tipo') or None,
            emenda=(request.form.get('emenda') or '').strip() or None,
            parlamentar=(request.form.get('parlamentar') or '').strip() or None,
            sei_emenda=(request.form.get('sei_emenda') or '').strip() or None,
            link_sei=(request.form.get('link_sei') or '').strip() or None,
            valor_cedido=_decimal(request.form.get('valor_cedido')),
            ano=request.form.get('ano', type=int),
            unidade=unid.nome if unid else (request.form.get('unidade') or '').strip() or None,
            unidade_id=unid.id if unid else None,
        )
        db.session.add(e)
        db.session.flush()
        item_nome = (request.form.get('item') or '').strip()
        if item_nome:
            qtde = _decimal(request.form.get('qtde')) or 0
            vu = _decimal(request.form.get('vl_unitario')) or 0
            db.session.add(SueqEmendaItem(
                emenda_id=e.id,
                emenda=e.emenda,
                item=item_nome,
                qtde_cadastrada=qtde,
                vl_unitario_cadastrado=vu,
                vl_total_cadastrado=qtde * vu,
                status=request.form.get('status_item') or 'Aguardando licitação',
                unidade_beneficiada=e.unidade,
                unidade_beneficiada_id=e.unidade_id,
            ))
        db.session.commit()
        flash('Emenda cadastrada.', 'success')
        return redirect(url_for('sueq.emenda_detalhe', id=e.id))
    return render_template(
        'sueq/emenda_form.html', emenda=None, unidades=unidades,
        parlamentares=parlamentares, tipos=TIPOS_EMENDA, status_item=STATUS_ITEM,
    )


@sueq_bp.route('/emendas/<uuid:id>')
@login_required
def emenda_detalhe(id):
    _exige('ver_emendas', 'editar_emendas', 'adicionar_emendas')
    emenda = SueqEmenda.query.get_or_404(id)
    return render_template('sueq/emenda_detalhe.html', emenda=emenda)


@sueq_bp.route('/emendas/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
def emenda_editar(id):
    _exige('editar_emendas')
    emenda = SueqEmenda.query.get_or_404(id)
    unidades = SueqUnidade.query.filter_by(ativo=True).order_by(SueqUnidade.nome).all()
    parlamentares = SueqParlamentar.query.filter_by(ativo=True).order_by(SueqParlamentar.nome).all()
    if request.method == 'POST':
        uid = request.form.get('unidade_id', type=int)
        unid = SueqUnidade.query.get(uid) if uid else None
        emenda.tipo = request.form.get('tipo') or None
        emenda.emenda = (request.form.get('emenda') or '').strip() or None
        emenda.parlamentar = (request.form.get('parlamentar') or '').strip() or None
        emenda.sei_emenda = (request.form.get('sei_emenda') or '').strip() or None
        emenda.link_sei = (request.form.get('link_sei') or '').strip() or None
        emenda.valor_cedido = _decimal(request.form.get('valor_cedido'))
        emenda.ano = request.form.get('ano', type=int)
        emenda.unidade = unid.nome if unid else (request.form.get('unidade') or '').strip() or None
        emenda.unidade_id = unid.id if unid else None
        db.session.commit()
        flash('Emenda atualizada.', 'success')
        return redirect(url_for('sueq.emenda_detalhe', id=emenda.id))
    return render_template(
        'sueq/emenda_form.html', emenda=emenda, unidades=unidades,
        parlamentares=parlamentares, tipos=TIPOS_EMENDA, status_item=STATUS_ITEM,
    )


# ── Licitações ───────────────────────────────────────────────────────────────

@sueq_bp.route('/licitacoes')
@login_required
def licitacoes():
    _exige('ver_licitacoes', 'editar_licitacoes', 'adicionar_licitacoes')
    q = request.args.get('q', '').strip()
    query = SueqProcesso.query.order_by(SueqProcesso.created_at.desc())
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            SueqProcesso.identificador.ilike(like),
            SueqProcesso.objeto.ilike(like),
            SueqProcesso.modalidade.ilike(like),
        ))
    return render_template(
        'sueq/licitacoes_listar.html', lista=query.all(), filtro_q=q,
    )


@sueq_bp.route('/licitacoes/nova', methods=['GET', 'POST'])
@login_required
def licitacao_nova():
    _exige('adicionar_licitacoes')
    if request.method == 'POST':
        p = SueqProcesso(
            identificador=(request.form.get('identificador') or '').strip(),
            tipo=(request.form.get('tipo') or '').strip() or None,
            objeto=(request.form.get('objeto') or '').strip() or None,
            modalidade=request.form.get('modalidade') or None,
            status=request.form.get('status') or 'Em andamento',
            secao=(request.form.get('secao') or '').strip() or 'SUEQ',
            valor_estimado=_decimal(request.form.get('valor_estimado')),
            observacao=(request.form.get('observacao') or '').strip() or None,
            link_publico_sei=(request.form.get('link_publico_sei') or '').strip() or None,
        )
        if not p.identificador:
            flash('Informe o identificador (CPL / processo).', 'warning')
        else:
            db.session.add(p)
            db.session.commit()
            flash('Licitação cadastrada.', 'success')
            return redirect(url_for('sueq.licitacoes'))
    return render_template(
        'sueq/licitacao_form.html', processo=None,
        modalidades=MODALIDADES, status_opcoes=STATUS_PROCESSO,
    )


@sueq_bp.route('/licitacoes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def licitacao_editar(id):
    _exige('editar_licitacoes')
    processo = SueqProcesso.query.get_or_404(id)
    if request.method == 'POST':
        processo.identificador = (request.form.get('identificador') or '').strip()
        processo.tipo = (request.form.get('tipo') or '').strip() or None
        processo.objeto = (request.form.get('objeto') or '').strip() or None
        processo.modalidade = request.form.get('modalidade') or None
        processo.status = request.form.get('status') or None
        processo.secao = (request.form.get('secao') or '').strip() or None
        processo.valor_estimado = _decimal(request.form.get('valor_estimado'))
        processo.observacao = (request.form.get('observacao') or '').strip() or None
        processo.link_publico_sei = (request.form.get('link_publico_sei') or '').strip() or None
        db.session.commit()
        flash('Licitação atualizada.', 'success')
        return redirect(url_for('sueq.licitacoes'))
    return render_template(
        'sueq/licitacao_form.html', processo=processo,
        modalidades=MODALIDADES, status_opcoes=STATUS_PROCESSO,
    )


# ── Chamados SUEQ ────────────────────────────────────────────────────────────

@sueq_bp.route('/chamados')
@login_required
def chamados():
    _exige('ver_chamados_sueq', 'editar_chamados_sueq', 'adicionar_chamados_sueq')
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    query = SueqChamado.query.order_by(SueqChamado.created_at.desc())
    if status:
        query = query.filter(SueqChamado.status == status)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            SueqChamado.protocolo.ilike(like),
            SueqChamado.unidade.ilike(like),
            SueqChamado.equipamento.ilike(like),
            SueqChamado.patrimonio.ilike(like),
            SueqChamado.problema.ilike(like),
        ))
    return render_template(
        'sueq/chamados_listar.html', lista=query.all(),
        filtro_q=q, filtro_status=status, status_opcoes=STATUS_CHAMADO,
    )


@sueq_bp.route('/chamados/novo', methods=['GET', 'POST'])
@login_required
def chamado_novo():
    _exige('adicionar_chamados_sueq')
    unidades = SueqUnidade.query.filter_by(ativo=True).order_by(SueqUnidade.nome).all()
    if request.method == 'POST':
        uid = request.form.get('unidade_id', type=int)
        unid = SueqUnidade.query.get(uid) if uid else None
        c = SueqChamado(
            protocolo=_proximo_protocolo(),
            data_solicitacao=datetime.now().strftime('%d/%m/%Y'),
            unidade=unid.nome if unid else (request.form.get('unidade') or '').strip() or None,
            unidade_id=unid.id if unid else None,
            endereco=unid.endereco if unid else None,
            telefone=unid.telefone if unid else None,
            equipamento=(request.form.get('equipamento') or '').strip() or None,
            fabricante=(request.form.get('fabricante') or '').strip() or None,
            serie=(request.form.get('serie') or '').strip() or None,
            patrimonio=(request.form.get('patrimonio') or '').strip() or None,
            categoria=(request.form.get('categoria') or '').strip() or None,
            servico=(request.form.get('servico') or '').strip() or None,
            problema=(request.form.get('problema') or '').strip() or None,
            descricao=(request.form.get('descricao') or '').strip() or None,
            responsavel=(request.form.get('responsavel') or '').strip() or None,
            grau_urgencia=request.form.get('grau_urgencia') or 'Média',
            status='Aguardando abertura',
        )
        db.session.add(c)
        db.session.flush()
        db.session.add(SueqChamadoControle(
            protocolo=c.protocolo,
            chamado_protocolo=c.protocolo,
            chamado_id=c.id,
            status='Aguardando abertura',
        ))
        db.session.commit()
        flash(f'Chamado {c.protocolo} aberto.', 'success')
        return redirect(url_for('sueq.chamado_detalhe', id=c.id))
    return render_template(
        'sueq/chamado_form.html', chamado=None, unidades=unidades,
        urgencias=URGENCIAS, status_opcoes=STATUS_CHAMADO,
    )


@sueq_bp.route('/chamados/<uuid:id>')
@login_required
def chamado_detalhe(id):
    _exige('ver_chamados_sueq', 'editar_chamados_sueq', 'adicionar_chamados_sueq')
    chamado = SueqChamado.query.get_or_404(id)
    return render_template('sueq/chamado_detalhe.html', chamado=chamado)


@sueq_bp.route('/chamados/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
def chamado_editar(id):
    _exige('editar_chamados_sueq')
    chamado = SueqChamado.query.get_or_404(id)
    unidades = SueqUnidade.query.filter_by(ativo=True).order_by(SueqUnidade.nome).all()
    if request.method == 'POST':
        uid = request.form.get('unidade_id', type=int)
        unid = SueqUnidade.query.get(uid) if uid else None
        chamado.unidade = unid.nome if unid else chamado.unidade
        chamado.unidade_id = unid.id if unid else chamado.unidade_id
        chamado.equipamento = (request.form.get('equipamento') or '').strip() or None
        chamado.fabricante = (request.form.get('fabricante') or '').strip() or None
        chamado.serie = (request.form.get('serie') or '').strip() or None
        chamado.patrimonio = (request.form.get('patrimonio') or '').strip() or None
        chamado.categoria = (request.form.get('categoria') or '').strip() or None
        chamado.servico = (request.form.get('servico') or '').strip() or None
        chamado.problema = (request.form.get('problema') or '').strip() or None
        chamado.descricao = (request.form.get('descricao') or '').strip() or None
        chamado.responsavel = (request.form.get('responsavel') or '').strip() or None
        chamado.grau_urgencia = request.form.get('grau_urgencia') or chamado.grau_urgencia
        chamado.status = request.form.get('status') or chamado.status
        chamado.os_numero = (request.form.get('os_numero') or '').strip() or None
        chamado.servico_realizado = (request.form.get('servico_realizado') or '').strip() or None
        if chamado.controle:
            chamado.controle.status = chamado.status
            chamado.controle.os = chamado.os_numero
            chamado.controle.feito = chamado.servico_realizado
        db.session.commit()
        flash('Chamado atualizado.', 'success')
        return redirect(url_for('sueq.chamado_detalhe', id=chamado.id))
    return render_template(
        'sueq/chamado_form.html', chamado=chamado, unidades=unidades,
        urgencias=URGENCIAS, status_opcoes=STATUS_CHAMADO,
    )


@sueq_bp.route('/chamados/<uuid:id>/imprimir')
@login_required
def chamado_imprimir(id):
    _exige('ver_chamados_sueq', 'editar_chamados_sueq', 'adicionar_chamados_sueq')
    chamado = SueqChamado.query.get_or_404(id)
    qr_url = None
    unidade_sigus = None
    if chamado.unidade:
        unidade_sigus = Unidade.query.filter(Unidade.nome.ilike(chamado.unidade)).first()
        if unidade_sigus and unidade_sigus.link_maps:
            qr_url = url_for('unidades.maps_redirect', id=unidade_sigus.id, _external=True)
    return render_template(
        'sueq/chamado_imprimir.html',
        chamado=chamado, now=datetime.utcnow(), qr_url=qr_url,
        unidade_sigus=unidade_sigus,
    )
