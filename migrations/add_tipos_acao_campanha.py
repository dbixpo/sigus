# -*- coding: utf-8 -*-
"""Cada campanha de saúde vira um tema do mural, com o laço na notícia.

    python migrations/add_tipos_acao_campanha.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text

from app import create_app, db
from app.models.campanha import CampanhaSaude, garantir_campanhas, sincronizar_tipos_campanha
from app.models.noticias import TipoAcao

app = create_app()
with app.app_context():
    CampanhaSaude.__table__.create(db.engine, checkfirst=True)
    with db.engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE tipos_acao
            ADD COLUMN IF NOT EXISTS campanha_id INTEGER
            UNIQUE REFERENCES campanhas_saude(id) ON DELETE SET NULL
        """))
    garantir_campanhas()
    sincronizar_tipos_campanha()
    ligados = TipoAcao.query.filter(TipoAcao.campanha_id.isnot(None)).count()
    print(f'OK. {ligados} tema(s) de campanha no mural.')
