# -*- coding: utf-8 -*-
"""
Migração: adiciona CPL, link_sei e modalidade em contratos.
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
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS cpl VARCHAR(30)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS link_sei VARCHAR(500)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS modalidade VARCHAR(80)"
        ))
        conn.commit()

    print("OK: cpl, link_sei e modalidade adicionados em contratos.")
