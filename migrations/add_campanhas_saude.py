# -*- coding: utf-8 -*-
"""Campanhas de cor (laços) e a permissão copiada de quem já cuida dos feriados.

    python migrations/add_campanhas_saude.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.campanha import CampanhaSaude, garantir_campanhas
from app.models.perfil_permissao import PerfilPermissao

app = create_app()
with app.app_context():
    CampanhaSaude.__table__.create(db.engine, checkfirst=True)
    garantir_campanhas()
    for origem in PerfilPermissao.query.filter_by(secao='CONF_Feriados').all():
        ja = PerfilPermissao.query.filter_by(
            perfil=origem.perfil, secao='CONF_Campanhas',
        ).first()
        if ja:
            continue
        db.session.add(PerfilPermissao(
            perfil=origem.perfil,
            secao='CONF_Campanhas',
            ver=origem.ver,
            editar=origem.editar,
            adicionar=origem.adicionar,
        ))
    db.session.commit()
    print(f'OK. {CampanhaSaude.query.count()} campanha(s).')
