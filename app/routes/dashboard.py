from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app import db
from app.models.unidade import UsuarioUnidade
from app.models.chamado import Chamado
from app.models.usuario import Usuario
from app.models.falta_abonada import FaltaAbonada
from app.routes.noticias import (
    pode_publicar, comunicados_da_unidade, montar_cards_comunicados, feed_mural,
    stats_acoes_feed,
)
from app.utils import hoje_brasilia

dashboard_bp = Blueprint('dashboard', __name__)


def _contar_chamados_unidade(unidade_id, status):
    if not unidade_id:
        return 0
    return Chamado.query.filter(
        Chamado.status == status,
        Chamado.unidade_id == unidade_id,
    ).count()


def _ultimos_chamados_unidade(unidade_id, limit=8):
    if not unidade_id:
        return []
    return (
        Chamado.query
        .filter(
            Chamado.status.in_(['aberto', 'em_andamento']),
            Chamado.unidade_id == unidade_id,
        )
        .order_by(Chamado.criado_em.desc())
        .limit(limit)
        .all()
    )


def _aniversariantes_unidade(unidade_id, hoje, so_hoje=False):
    if not unidade_id:
        return []
    q = (
        db.session.query(Usuario)
        .join(UsuarioUnidade, UsuarioUnidade.usuario_id == Usuario.id)
        .filter(
            Usuario.ativo.is_(True),
            Usuario.perfil != 'administrador',
            Usuario.data_nasc.isnot(None),
            UsuarioUnidade.ativo.is_(True),
            UsuarioUnidade.unidade_id == unidade_id,
        )
    )
    if so_hoje:
        q = q.filter(
            db.extract('month', Usuario.data_nasc) == hoje.month,
            db.extract('day', Usuario.data_nasc) == hoje.day,
        )
    else:
        q = q.filter(db.extract('month', Usuario.data_nasc) == hoje.month)
    q = q.order_by(db.extract('day', Usuario.data_nasc), Usuario.nome)
    visto = set()
    out = []
    for u in q.all():
        if u.id in visto:
            continue
        visto.add(u.id)
        out.append(u)
    return out


def _abonando_hoje(unidade_id, hoje):
    if not unidade_id:
        return []
    return (
        FaltaAbonada.query
        .options(joinedload(FaltaAbonada.usuario))
        .filter_by(unidade_id=unidade_id, data_falta=hoje, status=FaltaAbonada.STATUS_ATIVA)
        .all()
    )


@dashboard_bp.route('/dashboard')
@login_required
def index():
    hoje = hoje_brasilia()
    unidade = current_user.unidade_logada
    unidade_id = unidade.id if unidade else None

    chamados_abertos = _contar_chamados_unidade(unidade_id, 'aberto')
    ultimos_chamados = _ultimos_chamados_unidade(unidade_id)
    aniv_hoje = _aniversariantes_unidade(unidade_id, hoje, so_hoje=True)
    aniv_mes = _aniversariantes_unidade(unidade_id, hoje, so_hoje=False)
    abonando = _abonando_hoje(unidade_id, hoje)

    comunicados = montar_cards_comunicados(
        comunicados_da_unidade(unidade_id, limite=12),
        current_user.id,
    )
    mural = feed_mural(limite=30)
    mural_stats = stats_acoes_feed(mural, current_user.id)
    meses = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
        5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
        9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro',
    }

    _preview = request.args.get('preview_aniv', '')
    try:
        _d, _m = [int(x) for x in _preview.split('-')]
        _dia_ref, _mes_ref = _d, _m
    except Exception:
        _dia_ref, _mes_ref = hoje.day, hoje.month

    eh_meu_aniversario = (
        current_user.data_nasc is not None
        and current_user.data_nasc.day == _dia_ref
        and current_user.data_nasc.month == _mes_ref
    )

    return render_template(
        'dashboard/index.html',
        unidade=unidade,
        chamados_abertos=chamados_abertos,
        ultimos_chamados=ultimos_chamados,
        aniv_hoje=aniv_hoje,
        aniv_mes=aniv_mes,
        abonando=abonando,
        comunicados=comunicados,
        mural=mural,
        mural_stats=mural_stats,
        meses=meses,
        pode_publicar=pode_publicar(),
        eh_meu_aniversario=eh_meu_aniversario,
        hoje=hoje,
        preview_aniv=bool(_preview),
    )
