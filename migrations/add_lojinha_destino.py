# -*- coding: utf-8 -*-
"""Unidade que pegou o item da lojinha (idempotente)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE itens_lojinha
            ADD COLUMN IF NOT EXISTS destino_unidade_id INTEGER
            REFERENCES unidades(id) ON DELETE SET NULL
        """))
        conn.execute(text("""
            ALTER TABLE itens_lojinha
            ADD COLUMN IF NOT EXISTS destino_em TIMESTAMP
        """))
        conn.commit()
    print('OK: itens_lojinha com destino_unidade_id e destino_em.')
