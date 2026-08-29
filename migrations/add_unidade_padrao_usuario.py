# -*- coding: utf-8 -*-
"""Adiciona unidade_padrao_id ao usuário para definir qual unidade está 'ativa' no momento."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS unidade_padrao_id INTEGER REFERENCES unidades(id) ON DELETE SET NULL"
        ))
        conn.commit()
    print("OK: unidade_padrao_id adicionado a usuarios.")
