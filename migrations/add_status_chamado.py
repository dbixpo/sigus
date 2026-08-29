# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.status_chamado import StatusChamado

STATUS_INICIAIS = [
    dict(slug='aberto',          label='Aberto',           badge_cor='danger',    ativo=True,  padrao_listagem=True,  encerra_chamado=False, ordem=0),
    dict(slug='em_andamento',    label='Em Andamento',     badge_cor='warning',   ativo=True,  padrao_listagem=True,  encerra_chamado=False, ordem=1),
    dict(slug='sem_contrato',    label='Sem Contrato',     badge_cor='info',      ativo=True,  padrao_listagem=True,  encerra_chamado=False, ordem=2),
    dict(slug='concluido',       label='Concluido',        badge_cor='success',   ativo=True,  padrao_listagem=False, encerra_chamado=True,  ordem=3),
    dict(slug='cancelado',       label='Cancelado',        badge_cor='secondary', ativo=True,  padrao_listagem=False, encerra_chamado=True,  ordem=4),
    dict(slug='aguardando_peca', label='Aguardando Peca',  badge_cor='info',      ativo=False, padrao_listagem=False, encerra_chamado=False, ordem=5),
]

app = create_app()
with app.app_context():
    db.create_all()
    inseridos = 0
    for dados in STATUS_INICIAIS:
        if not StatusChamado.query.filter_by(slug=dados['slug']).first():
            db.session.add(StatusChamado(**dados))
            inseridos += 1
    db.session.commit()
    total = StatusChamado.query.count()
    print("OK: %d inseridos, %d total." % (inseridos, total))
