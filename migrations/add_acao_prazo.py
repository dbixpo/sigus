# -*- coding: utf-8 -*-
"""Adiciona coluna prazo (data prevista) em acoes_plano."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE acoes_plano
            ADD COLUMN IF NOT EXISTS prazo DATE NULL
        """))
        conn.commit()
    print("OK: Coluna prazo adicionada em acoes_plano.")
