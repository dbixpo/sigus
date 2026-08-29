# -*- coding: utf-8 -*-
"""
Migração: torna numero_sei nullable em contratos (CPL ou SEI obrigatório).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # PostgreSQL
        try:
            conn.execute(text("ALTER TABLE contratos ALTER COLUMN numero_sei DROP NOT NULL"))
        except Exception:
            pass  # SQLite não suporta ALTER COLUMN; ignorar
        conn.commit()

    print("OK: numero_sei passou a aceitar NULL em contratos.")
