# -*- coding: utf-8 -*-
"""
Migração: cria tabela divisoes e adiciona divisao_id em setores_manutencao.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    from app.models.chamado import Divisao
    Divisao.__table__.create(db.engine, checkfirst=True)

    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE setores_manutencao
            ADD COLUMN IF NOT EXISTS divisao_id INTEGER REFERENCES divisoes(id) ON DELETE SET NULL
        """))
        conn.commit()

    print("OK: tabela divisoes criada e divisao_id adicionado em setores_manutencao.")
