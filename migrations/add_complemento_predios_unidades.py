# -*- coding: utf-8 -*-
"""
Migração: adiciona campo complemento em predios e unidades.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for tabela in ['predios', 'unidades']:
            conn.execute(text(
                f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS complemento VARCHAR(100)"
            ))
        conn.commit()

    print("OK: campo complemento adicionado em predios e unidades.")
