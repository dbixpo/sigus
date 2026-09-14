# -*- coding: utf-8 -*-
"""CPF informado na ciência de comunicados (idempotente)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS cpf VARCHAR(11)
        """))
        conn.commit()
    print('OK: comunicado_ciencias com CPF da ciência.')
