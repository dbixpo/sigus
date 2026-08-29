from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app import db
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.equipamento import Equipamento
from app.models.chamado import Chamado
from app.models.contrato import Contrato
from app.models.sala import Sala
from app.models.usuario import Usuario
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)


def _contar_equipamentos_unidade(unidade_ids, **filtros):
    """Conta equipamentos ativos filtrados pela(s) unidade(s) em que o usuário está logado."""
    if not unidade_ids:
        return 0
    q = (
        Equipamento.query
        .join(Sala, Equipamento.sala_id == Sala.id)
        .filter(Sala.unidade_id.in_(unidade_ids), Equipamento.ativo.is_(True))
    )
    for campo, valor in filtros.items():
        q = q.filter(getattr(Equipamento, campo) == valor)
    return q.count()


def _contar_chamados_unidade(unidade_ids, status):
    if not unidade_ids:
        return 0
    return Chamado.query.filter(
        Chamado.status == status,
        Chamado.unidade_id.in_(unidade_ids),
    ).count()


def _ultimos_chamados_unidade(unidade_ids, limit=8):
    if not unidade_ids:
        return []
    return (
        Chamado.query
        .filter(
            Chamado.status.in_(['aberto', 'em_andamento']),
            Chamado.unidade_id.in_(unidade_ids),
        )
        .order_by(Chamado.criado_em.desc())
        .limit(limit)
        .all()
    )


@dashboard_bp.route('/dashboard')
@login_required
def index():
    hoje = date.today()
    unidades_efetivas = current_user.ids_unidades_efetivos()

    # Sempre escopo da unidade logada (unidade padrão ou vínculos do usuário)
    total_equipamentos = _contar_equipamentos_unidade(unidades_efetivas, status='ativo')
    total_em_manutencao = _contar_equipamentos_unidade(unidades_efetivas, status='em_manutencao')
    total_inservíveis = _contar_equipamentos_unidade(unidades_efetivas, condicao='inservivel')
    chamados_abertos = _contar_chamados_unidade(unidades_efetivas, 'aberto')
    ultimos_chamados = _ultimos_chamados_unidade(unidades_efetivas)

    if current_user.pode('ver_dashboard_geral'):
        total_unidades = Unidade.query.filter_by(status='ativa').count()
        total_baixados = Equipamento.query.filter_by(ativo=True, status='baixado').count()
        chamados_andamento = Chamado.query.filter_by(status='em_andamento').count()
        contratos_vencendo = Contrato.query.filter_by(status='a_vencer').count()
        contratos_vencidos = Contrato.query.filter_by(status='vencido').count()

        contratos_criticos = (
            Contrato.query
            .filter(Contrato.status.in_(['a_vencer', 'vencido']))
            .order_by(Contrato.data_fim.asc())
            .limit(5).all()
        )
        unidades_ativas = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    else:
        unidades_vinculadas = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
        total_unidades = len(unidades_vinculadas)
        total_baixados = _contar_equipamentos_unidade(unidades_vinculadas, status='baixado')
        chamados_andamento = _contar_chamados_unidade(unidades_vinculadas, 'em_andamento')
        contratos_vencendo = 0
        contratos_vencidos = 0

        contratos_criticos = []
        unidades_ativas = Unidade.query.filter(
            Unidade.id.in_(unidades_vinculadas),
            Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()

    # Verifica se o próprio usuário logado faz aniversário hoje
    _preview = request.args.get('preview_aniv', '')
    try:
        _d, _m = [int(x) for x in _preview.split('-')]
        _dia_ref, _mes_ref = _d, _m
    except Exception:
        _dia_ref, _mes_ref = hoje.day, hoje.month

    eh_meu_aniversario = (
        current_user.data_nasc is not None
        and current_user.data_nasc.day   == _dia_ref
        and current_user.data_nasc.month == _mes_ref
    )

    return render_template('dashboard/index.html',
        total_unidades=total_unidades,
        total_equipamentos=total_equipamentos,
        total_em_manutencao=total_em_manutencao,
        total_baixados=total_baixados,
        total_inserviveis=total_inservíveis,
        chamados_abertos=chamados_abertos,
        chamados_andamento=chamados_andamento,
        contratos_vencendo=contratos_vencendo,
        contratos_vencidos=contratos_vencidos,
        ultimos_chamados=ultimos_chamados,
        contratos_criticos=contratos_criticos,
        unidades_ativas=unidades_ativas,
        eh_meu_aniversario=eh_meu_aniversario,
        hoje=hoje,
        preview_aniv=bool(_preview),
    )
