# -*- coding: utf-8 -*-
"""Cria tabela planos_anexos para anexos (PDF, fotos) de planos."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS planos_anexos (
                id SERIAL PRIMARY KEY,
                plano_id INTEGER NOT NULL REFERENCES planos(id) ON DELETE CASCADE,
                filename VARCHAR(200) NOT NULL,
                original VARCHAR(200) NOT NULL,
                mime_type VARCHAR(100),
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    print("OK: Tabela planos_anexos criada.")
