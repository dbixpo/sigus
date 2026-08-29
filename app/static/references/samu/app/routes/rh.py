"""Recursos Humanos - Faltas Abonadas (conforme SIGUS)."""
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models.falta_abonada import FaltaAbonada
from app.models.usuario import Usuario
from app.models.unidade_samu import UnidadeSamu

rh_bp = Blueprint('rh', __name__, url_prefix='/rh')

_LIMITE_ANO = 6
_LIMITE_MES = 1


def _checar_acesso(falta):
    if falta.usuario_id != current_user.id and not current_user.pode('rh_gerenciar_faltas'):
        abort(403)


@rh_bp.route('/faltas-abonadas')
@login_required
def faltas_abonadas():
    ano = request.args.get('ano', date.today().year, type=int)
    ver_hist = request.args.get('historico', '0') == '1'

    usuario_id = request.args.get('usuario_id', current_user.id, type=int)
    if usuario_id != current_user.id and not current_user.pode('rh_gerenciar_faltas'):
        abort(403)

    base_q = (
        FaltaAbonada.query
        .filter_by(usuario_id=usuario_id)
        .filter(db.extract('year', FaltaAbonada.data_falta) == ano)
    )

    faltas_ativas = base_q.filter_by(status='ativa').order_by(FaltaAbonada.data_falta).all()
    faltas_canceladas = base_q.filter_by(status='cancelada').order_by(FaltaAbonada.data_falta).all()

    anos_disponiveis = (
        db.session.query(db.extract('year', FaltaAbonada.data_falta).label('ano'))
        .filter_by(usuario_id=usuario_id)
        .distinct()
        .order_by(db.desc('ano'))
        .all()
    )
    anos_disponiveis = [int(r.ano) for r in anos_disponiveis]
    if date.today().year not in anos_disponiveis:
        anos_disponiveis.insert(0, date.today().year)

    usadas = len(faltas_ativas)
    restantes = _LIMITE_ANO - usadas
    meses_usados = {f.mes for f in faltas_ativas}

    todas_ativas = FaltaAbonada.query.filter_by(usuario_id=usuario_id, status='ativa').all()
    meses_ocupados = [{'ano': f.ano, 'mes': f.mes} for f in todas_ativas]

    usuario_atual = Usuario.query.get(usuario_id)
    unidades_samu = UnidadeSamu.query.filter_by(ativo=True).order_by(UnidadeSamu.nome).all()

    matricula_usuario = usuario_atual.matricula if usuario_atual else None

    return render_template(
        'rh/faltas_abonadas.html',
        faltas_ativas=faltas_ativas,
        faltas_canceladas=faltas_canceladas,
        ano=ano,
        anos_disponiveis=anos_disponiveis,
        usadas=usadas,
        restantes=restantes,
        meses_ocupados=meses_ocupados,
        limite=_LIMITE_ANO,
        meses_usados=meses_usados,
        usuario_id=usuario_id,
        ver_hist=ver_hist,
        usuario_atual=usuario_atual,
        unidades_samu=unidades_samu,
        matricula_usuario=matricula_usuario,
    )


@rh_bp.route('/faltas-abonadas/nova', methods=['POST'])
@login_required
def nova_falta():
    data_str = request.form.get('data_falta', '').strip()
    funcao = request.form.get('funcao', '').strip()
    unidade_samu_id = request.form.get('unidade_samu_id', type=int)

    if not data_str or not funcao:
        flash('Data e função são obrigatórias.', 'danger')
        return redirect(url_for('rh.faltas_abonadas'))

    try:
        data_falta = date.fromisoformat(data_str)
    except ValueError:
        flash('Data inválida.', 'danger')
        return redirect(url_for('rh.faltas_abonadas'))

    ano = data_falta.year
    mes = data_falta.month

    total_ano = FaltaAbonada.query.filter_by(usuario_id=current_user.id, status='ativa').filter(
        db.extract('year', FaltaAbonada.data_falta) == ano
    ).count()
    if total_ano >= _LIMITE_ANO:
        flash(f'Você já atingiu o limite de {_LIMITE_ANO} abonadas ativas em {ano}.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano))

    total_mes = FaltaAbonada.query.filter_by(usuario_id=current_user.id, status='ativa').filter(
        db.extract('year', FaltaAbonada.data_falta) == ano,
        db.extract('month', FaltaAbonada.data_falta) == mes,
    ).count()
    if total_mes >= _LIMITE_MES:
        flash('Já existe uma abonada ativa registrada neste mês.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano))

    falta = FaltaAbonada(
        usuario_id=current_user.id,
        unidade_samu_id=unidade_samu_id,
        data_falta=data_falta,
        funcao=funcao,
        status='ativa',
        criado_por=current_user.id,
    )
    db.session.add(falta)
    db.session.commit()
    return redirect(url_for('rh.faltas_abonadas', ano=ano))


@rh_bp.route('/faltas-abonadas/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_falta(id):
    falta = FaltaAbonada.query.get_or_404(id)
    _checar_acesso(falta)

    if falta.status == 'cancelada':
        flash('Esta abonada já está cancelada.', 'warning')
        return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))

    motivo = request.form.get('motivo', '').strip() or None

    falta.status = 'cancelada'
    falta.motivo_cancelamento = motivo
    falta.cancelado_em = datetime.utcnow()
    falta.cancelado_por = current_user.id

    db.session.commit()
    return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))


@rh_bp.route('/faltas-abonadas/<int:id>/reativar', methods=['POST'])
@login_required
def reativar_falta(id):
    falta = FaltaAbonada.query.get_or_404(id)
    _checar_acesso(falta)

    if falta.status == 'ativa':
        flash('Esta abonada já está ativa.', 'warning')
        return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))

    ano, mes = falta.ano, falta.mes

    total_ano = FaltaAbonada.query.filter_by(usuario_id=falta.usuario_id, status='ativa').filter(
        db.extract('year', FaltaAbonada.data_falta) == ano
    ).count()
    if total_ano >= _LIMITE_ANO:
        flash(f'Não é possível reativar: limite de {_LIMITE_ANO} abonadas ativas em {ano} já foi atingido.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano, historico='1'))

    total_mes = FaltaAbonada.query.filter_by(usuario_id=falta.usuario_id, status='ativa').filter(
        db.extract('year', FaltaAbonada.data_falta) == ano,
        db.extract('month', FaltaAbonada.data_falta) == mes,
    ).count()
    if total_mes >= _LIMITE_MES:
        flash('Não é possível reativar: já existe uma abonada ativa neste mês.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano, historico='1'))

    falta.status = 'ativa'
    falta.motivo_cancelamento = None
    falta.cancelado_em = None
    falta.cancelado_por = None

    db.session.commit()
    return redirect(url_for('rh.faltas_abonadas', ano=ano))


@rh_bp.route('/faltas-abonadas/<int:id>/imprimir')
@login_required
def imprimir_abonada(id):
    falta = FaltaAbonada.query.get_or_404(id)
    _checar_acesso(falta)

    if falta.status == 'cancelada':
        flash('Não é possível imprimir uma abonada cancelada.', 'warning')
        return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))

    usuario = falta.usuario
    unidade = falta.unidade_samu
    matricula = usuario.matricula_principal or usuario.matriculas.first()
    if not matricula and getattr(usuario, 'matricula', None):
        # Fallback: coluna matricula (string) do usuário
        class _Mat:
            pass
        m = _Mat()
        m.numero = usuario.matricula
        matricula = m

    return render_template(
        'rh/imprimir_abonada.html',
        falta=falta,
        usuario=usuario,
        unidade=unidade,
        matricula=matricula,
    )
