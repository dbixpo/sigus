# -*- coding: utf-8 -*-
"""
Migração: adiciona mandado_judicial (boolean) em contratos.
Substitui o uso de tag para marcar se é mandado judicial.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS mandado_judicial BOOLEAN DEFAULT FALSE"
        ))
        conn.commit()

    print("OK: mandado_judicial adicionado em contratos.")
