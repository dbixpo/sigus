# -*- coding: utf-8 -*-
"""
Migração: adiciona contrato_id em contrato_financeiro.
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
            "ALTER TABLE contrato_financeiro ADD COLUMN IF NOT EXISTS contrato_id INTEGER REFERENCES contratos(id) ON DELETE SET NULL"
        ))
        conn.commit()

    print("OK: contrato_id adicionado em contrato_financeiro.")
