from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models.falta_abonada import FaltaAbonada
from app.models.frequencia import competencia_label
from app.services.faltas_planilha import painel_faltas
from app.utils import agora_local, hoje_brasilia

rh_bp = Blueprint('rh', __name__, url_prefix='/rh')

_LIMITE_ANO = 6
_LIMITE_MES = 1


def _checar_acesso(falta):
    if falta.usuario_id != current_user.id and not current_user.pode('gerenciar_usuarios'):
        abort(403)


@rh_bp.route('/faltas-abonadas')
@login_required
def faltas_abonadas():
    if not current_user.pode('ver_faltas_abonadas'):
        abort(403)
    ano       = request.args.get('ano', hoje_brasilia().year, type=int)
    ver_hist  = request.args.get('historico', '0') == '1'

    usuario_id = request.args.get('usuario_id', current_user.id, type=int)
    if usuario_id != current_user.id and not current_user.pode('gerenciar_usuarios'):
        abort(403)

    base_q = (
        FaltaAbonada.query
        .filter_by(usuario_id=usuario_id)
        .filter(db.extract('year', FaltaAbonada.data_falta) == ano)
    )

    # Ativas do ano (contam para o limite)
    faltas_ativas = (
        base_q.filter_by(status='ativa')
        .order_by(FaltaAbonada.data_falta)
        .all()
    )
    # Canceladas do ano (só aparecem no histórico)
    faltas_canceladas = (
        base_q.filter_by(status='cancelada')
        .order_by(FaltaAbonada.data_falta)
        .all()
    )

    anos_disponiveis = (
        db.session.query(db.extract('year', FaltaAbonada.data_falta).label('ano'))
        .filter_by(usuario_id=usuario_id)
        .distinct()
        .order_by(db.desc('ano'))
        .all()
    )
    anos_disponiveis = [int(r.ano) for r in anos_disponiveis]
    if hoje_brasilia().year not in anos_disponiveis:
        anos_disponiveis.insert(0, hoje_brasilia().year)

    from app.models.usuario import Usuario
    usuario_atual = Usuario.query.get(usuario_id)
    matriculas_usuario = [m for m in list(usuario_atual.matriculas) if m.ativo]
    unidades_usuario   = usuario_atual.unidades_ativas

    painel = painel_faltas(usuario_atual, ano)
    usadas = painel['usadas']
    restantes = _LIMITE_ANO - usadas
    n_confirmadas = sum(1 for f in faltas_ativas if f.data_falta in painel['datas_planilha'])
    meses_usados = {f.mes for f in faltas_ativas}
    meses_ocupados = [
        {'ano': a, 'mes': m, 'origem': origem}
        for (a, m), origem in sorted(painel['meses'].items())
    ]
    for a_plan in {a for (a, _mes) in painel['meses']}:
        if a_plan not in anos_disponiveis:
            anos_disponiveis.append(a_plan)
    anos_disponiveis.sort(reverse=True)

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
        matriculas_usuario=matriculas_usuario,
        unidades_usuario=unidades_usuario,
        fa_planilha=painel['datas_planilha'],
        fa_so_planilha=painel['so_planilha'],
        fa_pode_formalizar=painel['tem_planilha_sem_registro'],
        n_confirmadas=n_confirmadas,
        competencia_label=competencia_label,
    )


@rh_bp.route('/faltas-abonadas/nova', methods=['POST'])
@login_required
def nova_falta():
    data_str   = request.form.get('data_falta', '').strip()
    funcao     = request.form.get('funcao', '').strip()
    unidade_id = request.form.get('unidade_id', type=int)

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

    painel = painel_faltas(current_user, ano)
    origem_mes = painel['meses'].get((ano, mes))
    if origem_mes in ('registro', 'ambos'):
        flash('Já existe uma abonada ativa registrada neste mês.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano))
    if painel['usadas'] >= _LIMITE_ANO and origem_mes != 'planilha':
        flash(
            f'Você já atingiu o limite de {_LIMITE_ANO} faltas abonadas em {ano}, '
            'contando o que já foi lançado na frequência.',
            'danger',
        )
        return redirect(url_for('rh.faltas_abonadas', ano=ano))

    # Unidade: usa a selecionada no modal; fallback para principal
    if not unidade_id:
        u = current_user.unidade_principal
        unidade_id = u.id if u else None

    falta = FaltaAbonada(
        usuario_id  = current_user.id,
        unidade_id  = unidade_id,
        data_falta  = data_falta,
        funcao      = funcao,
        status      = 'ativa',
        criado_por  = current_user.id,
    )
    db.session.add(falta)
    db.session.commit()

    flash('Falta abonada registrada com sucesso.', 'success')
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

    falta.status              = 'cancelada'
    falta.motivo_cancelamento = motivo
    falta.cancelado_em        = agora_local()
    falta.cancelado_por       = current_user.id

    db.session.commit()
    flash('Abonada cancelada. O histórico foi preservado.', 'success')
    return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))


@rh_bp.route('/faltas-abonadas/<int:id>/reativar', methods=['POST'])
@login_required
def reativar_falta(id):
    falta = FaltaAbonada.query.get_or_404(id)
    _checar_acesso(falta)

    if falta.status == 'ativa':
        flash('Esta abonada já está ativa.', 'warning')
        return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))

    ano = falta.ano
    mes = falta.mes

    painel = painel_faltas(falta.usuario, ano)
    origem_mes = painel['meses'].get((ano, mes))
    if origem_mes in ('registro', 'ambos'):
        flash('Não é possível reativar: já existe uma abonada ativa neste mês.', 'danger')
        return redirect(url_for('rh.faltas_abonadas', ano=ano, historico='1'))
    if painel['usadas'] >= _LIMITE_ANO and origem_mes != 'planilha':
        flash(
            f'Não é possível reativar: limite de {_LIMITE_ANO} faltas abonadas em {ano} já foi atingido, '
            'contando o que já foi lançado na frequência.',
            'danger',
        )
        return redirect(url_for('rh.faltas_abonadas', ano=ano, historico='1'))

    falta.status              = 'ativa'
    falta.motivo_cancelamento = None
    falta.cancelado_em        = None
    falta.cancelado_por       = None

    db.session.commit()
    flash('Abonada reativada com sucesso.', 'success')
    return redirect(url_for('rh.faltas_abonadas', ano=ano))


@rh_bp.route('/faltas-abonadas/<int:id>/imprimir')
@login_required
def imprimir_abonada(id):
    falta = FaltaAbonada.query.get_or_404(id)
    _checar_acesso(falta)

    if falta.status == 'cancelada':
        flash('Não é possível imprimir uma abonada cancelada.', 'warning')
        return redirect(url_for('rh.faltas_abonadas', ano=falta.ano))

    usuario  = falta.usuario
    unidade  = falta.unidade
    matricula = None
    todas_mats = list(usuario.matriculas)
    if todas_mats:
        ativas = [m for m in todas_mats if m.ativo]
        matricula = ativas[0] if ativas else todas_mats[0]

    return render_template(
        'rh/imprimir_abonada.html',
        falta=falta,
        usuario=usuario,
        unidade=unidade,
        matricula=matricula,
    )
