# -*- coding: utf-8 -*-
"""Controle de Empenho (planilha FINANCEIRO - DAG)."""
from datetime import datetime as dt
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.contrato import Contrato
from app.models.contrato_financeiro import ContratoFinanceiro, TIPO_OPCOES, MOTIVO_OPCOES

contrato_financeiro_bp = Blueprint('contrato_financeiro', __name__, url_prefix='/contratos/empenhos')


@contrato_financeiro_bp.route('/')
@login_required
def listar():
    if not current_user.pode('ver_controle_empenho') and not current_user.pode('editar_controle_empenho') and not current_user.pode('adicionar_controle_empenho'):
        abort(403)
    tipo_filtro = request.args.get('tipo', '')
    motivo_filtro = request.args.get('motivo', '')
    query = ContratoFinanceiro.query.order_by(ContratoFinanceiro.criado_em.desc())
    if tipo_filtro:
        query = query.filter(ContratoFinanceiro.tipo == tipo_filtro)
    if motivo_filtro:
        query = query.filter(ContratoFinanceiro.motivo == motivo_filtro)
    itens = query.all()
    return render_template('contrato_financeiro/listar.html',
                           itens=itens, tipo_opcoes=TIPO_OPCOES, motivo_opcoes=MOTIVO_OPCOES,
                           filtro_tipo=tipo_filtro, filtro_motivo=motivo_filtro)


@contrato_financeiro_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.pode('adicionar_controle_empenho'):
        abort(403)
    contratos = Contrato.query.order_by(Contrato.data_fim.desc()).all()
    contrato_id_pre = request.args.get('contrato_id', type=int)
    if request.method == 'POST':
        item = _obter_item_do_form(None)
        db.session.add(item)
        db.session.commit()
        flash('Registro de empenho cadastrado!', 'success')
        return redirect(url_for('contrato_financeiro.listar'))
    return render_template('contrato_financeiro/form.html', item=None,
                           tipo_opcoes=TIPO_OPCOES, motivo_opcoes=MOTIVO_OPCOES,
                           contratos=contratos, contrato_id_pre=contrato_id_pre)


@contrato_financeiro_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_controle_empenho'):
        abort(403)
    item = ContratoFinanceiro.query.get_or_404(id)
    contratos = Contrato.query.order_by(Contrato.data_fim.desc()).all()
    if request.method == 'POST':
        _aplicar_form_ao_item(item)
        db.session.commit()
        flash('Registro atualizado!', 'success')
        return redirect(url_for('contrato_financeiro.listar'))
    return render_template('contrato_financeiro/form.html', item=item,
                           tipo_opcoes=TIPO_OPCOES, motivo_opcoes=MOTIVO_OPCOES,
                           contratos=contratos, contrato_id_pre=None)


@contrato_financeiro_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    if not current_user.pode('editar_controle_empenho'):
        abort(403)
    item = ContratoFinanceiro.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Registro excluído.', 'info')
    return redirect(url_for('contrato_financeiro.listar'))


def _parse_date(val):
    if not val:
        return None
    try:
        return dt.strptime(val, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _decimal(val):
    if not val:
        return None
    try:
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return None


def _obter_item_do_form(existing):
    if existing:
        item = existing
    else:
        item = ContratoFinanceiro()
    _aplicar_form_ao_item(item)
    return item


def _aplicar_form_ao_item(item):
    contrato_id = request.form.get('contrato_id', '').strip()
    item.contrato_id = int(contrato_id) if contrato_id and contrato_id.isdigit() else None
    item.tipo = request.form.get('tipo', '').strip() or None
    item.processo = request.form.get('processo', '').strip() or None
    item.motivo = request.form.get('motivo', '').strip() or None
    item.prestador = request.form.get('prestador', '').strip() or None
    item.objeto = request.form.get('objeto', '').strip() or None
    item.referencia = request.form.get('referencia', '').strip() or None
    item.valor_total = _decimal(request.form.get('valor_total'))
    item.especializada = request.form.get('especializada', '').strip() or None
    item.vigilancia = request.form.get('vigilancia', '').strip() or None
    item.atencao_basica = request.form.get('atencao_basica', '').strip() or None
    item.outros = request.form.get('outros', '').strip() or None
    item.tabela_sus = request.form.get('tabela_sus', '').strip() or None
    item.complemento = request.form.get('complemento', '').strip() or None
    item.emenda_municipal = request.form.get('emenda_municipal', '').strip() or None
    item.emenda_estadual = request.form.get('emenda_estadual', '').strip() or None
    item.emenda_federal = request.form.get('emenda_federal', '').strip() or None
    item.observacao = request.form.get('observacao', '').strip() or None
    item.data_necessaria = _parse_date(request.form.get('data_necessaria'))
    item.data_envio_divisao = _parse_date(request.form.get('data_envio_divisao'))
    item.data_envio_fms = _parse_date(request.form.get('data_envio_fms'))
    item.data_devolucao_setor = _parse_date(request.form.get('data_devolucao_setor'))
    item.reservas = request.form.get('reservas', '').strip() or None
