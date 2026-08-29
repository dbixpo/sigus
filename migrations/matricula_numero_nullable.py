# -*- coding: utf-8 -*-
"""Torna o campo numero nullable em matriculas_profissionais para permitir Contrato por Prazo Determinado sem matrícula."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE matriculas_profissionais
            ALTER COLUMN numero DROP NOT NULL
        """))
        conn.commit()
    print("OK: Campo numero em matriculas_profissionais agora permite NULL.")
