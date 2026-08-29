"""Abertura de chamados sem login — link curto /abrir-chamado."""
import re

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session,
)
from app import db
from app.models.unidade import Unidade
from app.models.chamado import Chamado, ChamadoHistorico
from app.chamado_acesso import (
    is_chamado_externo, conceder_acompanhamento, pode_acompanhar,
    buscar_chamado_acompanhamento, chamado_abertura_acesso,
)

chamados_externo_bp = Blueprint('chamados_externo', __name__, url_prefix='/abrir-chamado')


def _whatsapp_limpo(val):
    return re.sub(r'\D', '', val or '')


def _whatsapp_formatado(val):
    wa = _whatsapp_limpo(val)
    if len(wa) == 11:
        return f'({wa[:2]}) {wa[2:7]}-{wa[7:]}'
    if len(wa) == 10:
        return f'({wa[:2]}) {wa[2:6]}-{wa[6:]}'
    return (val or '').strip()


def _email_valido(email):
    email = (email or '').strip().lower()
    if not email or len(email) > 200:
        return False
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None


@chamados_externo_bp.route('/', methods=['GET', 'POST'])
def identificacao():
    unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    next_url = request.args.get('next') or request.form.get('next') or ''

    if request.method == 'GET' and request.args.get('novo'):
        session.pop('externo_nome', None)
        session.pop('externo_whatsapp', None)
        session.pop('externo_email', None)
        session.pop('externo_unidade_id', None)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip()
        email = request.form.get('email', '').strip().lower()
        unidade_id = request.form.get('unidade_id', type=int)
        form_data = request.form

        if not nome or len(nome) < 3:
            flash('Informe seu nome completo.', 'danger')
            return render_template('chamados_externo/identificacao.html',
                                   unidades=unidades, form_data=form_data, next_url=next_url)
        wa = _whatsapp_limpo(whatsapp)
        if len(wa) < 10:
            flash('Informe um WhatsApp válido com DDD.', 'danger')
            return render_template('chamados_externo/identificacao.html',
                                   unidades=unidades, form_data=form_data, next_url=next_url)
        if not _email_valido(email):
            flash('Informe um e-mail institucional válido.', 'danger')
            return render_template('chamados_externo/identificacao.html',
                                   unidades=unidades, form_data=form_data, next_url=next_url)
        if not unidade_id or unidade_id not in [u.id for u in unidades]:
            flash('Selecione a unidade onde você está.', 'danger')
            return render_template('chamados_externo/identificacao.html',
                                   unidades=unidades, form_data=form_data, next_url=next_url)

        session['externo_nome'] = nome
        session['externo_whatsapp'] = _whatsapp_formatado(wa)
        session['externo_email'] = email
        session['externo_unidade_id'] = unidade_id
        session.permanent = True

        if next_url and next_url.startswith('/') and 'solicitacao-administrativa' in next_url:
            return redirect(next_url)
        return redirect(url_for('chamados_externo.novo_solicitacao_administrativa'))

    if is_chamado_externo() and not request.args.get('novo'):
        return redirect(url_for('chamados_externo.novo_solicitacao_administrativa'))

    return render_template('chamados_externo/identificacao.html',
                           unidades=unidades, form_data={}, next_url=next_url)


@chamados_externo_bp.route('/confirmacao')
def confirmacao():
    numero = request.args.get('numero', '').strip()
    if not numero:
        return redirect(url_for('chamados_externo.identificacao'))
    chamado = Chamado.query.filter(Chamado.numero.ilike(numero)).first()
    if not chamado:
        flash('Chamado não encontrado.', 'warning')
        return redirect(url_for('chamados_externo.identificacao'))
    conceder_acompanhamento(chamado)
    return render_template('chamados_externo/confirmacao.html', numero=chamado.numero)


@chamados_externo_bp.route('/acompanhar', methods=['GET', 'POST'])
def acompanhar():
    unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    numero_prefill = (request.args.get('numero') or request.form.get('numero') or '').strip().upper()

    if request.method == 'POST':
        numero = request.form.get('numero', '').strip()
        unidade_id = request.form.get('unidade_id', type=int)
        form_data = request.form

        chamado, erro = buscar_chamado_acompanhamento(numero, unidade_id)
        if erro:
            flash(erro, 'danger')
            return render_template(
                'chamados_externo/acompanhar_form.html',
                unidades=unidades,
                form_data=form_data,
                numero_prefill=numero.strip().upper(),
            )

        conceder_acompanhamento(chamado)
        return redirect(url_for('chamados_externo.acompanhar_detalhe', numero=chamado.numero))

    form_data = {}
    if numero_prefill:
        form_data['numero'] = numero_prefill
    return render_template(
        'chamados_externo/acompanhar_form.html',
        unidades=unidades,
        form_data=form_data,
        numero_prefill=numero_prefill,
    )


@chamados_externo_bp.route('/acompanhar/<numero>')
def acompanhar_detalhe(numero):
    chamado = Chamado.query.filter(Chamado.numero.ilike(numero.strip())).first()
    if not chamado:
        flash('Chamado não encontrado.', 'warning')
        return redirect(url_for('chamados_externo.acompanhar'))

    if not pode_acompanhar(chamado):
        flash('Informe o número do chamado e a unidade para acompanhar.', 'warning')
        return redirect(url_for('chamados_externo.acompanhar', numero=chamado.numero))

    historico = chamado.historico.order_by(ChamadoHistorico.criado_em).all()
    fotos = chamado.fotos.all()
    pendentes = [h for h in historico if h.pendente]

    return render_template(
        'chamados_externo/acompanhar_detalhe.html',
        chamado=chamado,
        historico=historico,
        fotos=fotos,
        pendentes=pendentes,
    )


# Reutiliza a view de Solicitação Administrativa (único tipo no fluxo público por enquanto)
from app.routes import chamados as _chamados_views  # noqa: E402


@chamados_externo_bp.route('/tipo', methods=['GET'])
@chamados_externo_bp.route('/predial', methods=['GET', 'POST'])
@chamados_externo_bp.route('/bem-permanente', methods=['GET', 'POST'])
@chamados_externo_bp.route('/solicitacao-equipamento', methods=['GET', 'POST'])
@chamado_abertura_acesso
def _redirecionar_para_sa():
    flash('No momento, só é possível abrir Solicitação Administrativa por aqui.', 'info')
    return redirect(url_for('chamados_externo.novo_solicitacao_administrativa'))


chamados_externo_bp.add_url_rule(
    '/solicitacao-administrativa', 'novo_solicitacao_administrativa',
    _chamados_views.novo_solicitacao_administrativa, methods=['GET', 'POST'])
