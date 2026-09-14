# -*- coding: utf-8 -*-
"""Campos de auditoria na ciência de comunicados (idempotente)."""
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
            ADD COLUMN IF NOT EXISTS ip VARCHAR(45)
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS user_agent VARCHAR(400)
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS unidade_id INTEGER
            REFERENCES unidades(id) ON DELETE SET NULL
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS assinatura_base64 TEXT
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS origem VARCHAR(20)
        """))
        conn.commit()
    print('OK: comunicado_ciencias com IP, user-agent, unidade, assinatura e origem.')
