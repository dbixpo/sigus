"""Inclui GUT do solicitante na observação do primeiro registro de abertura (chamados antigos)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.chamado import Chamado, ChamadoHistorico

app = create_app()
with app.app_context():
    atualizados = 0
    chamados = Chamado.query.filter(
        Chamado.sa_gravidade.isnot(None),
        Chamado.sa_urgencia.isnot(None),
        Chamado.sa_tendencia.isnot(None),
    ).all()

    for chamado in chamados:
        if not chamado.gut_solicitante_preenchido:
            continue
        gut_txt = f'Priorização do solicitante: {chamado.gut_solicitante_resumo}'
        historico = (
            ChamadoHistorico.query.filter_by(chamado_id=chamado.id)
            .filter(ChamadoHistorico.acao.ilike('%aberto%'))
            .order_by(ChamadoHistorico.id.asc())
            .first()
        )
        if not historico:
            continue
        obs = (historico.observacao or '').strip()
        if 'Priorização do solicitante:' in obs:
            continue
        historico.observacao = f'{obs}\n\n{gut_txt}'.strip() if obs else gut_txt
        atualizados += 1

    db.session.commit()
    print(f'OK: backfill_historico_gut_abertura — {atualizados} registro(s) atualizado(s).')
