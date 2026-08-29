# -*- coding: utf-8 -*-
"""Adiciona atualizado_em e atualizado_por em planos."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE planos
            ADD COLUMN IF NOT EXISTS atualizado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
        """))
        conn.execute(text("""
            ALTER TABLE planos
            ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP NULL
        """))
        conn.commit()
    print("OK: Colunas atualizado_por e atualizado_em adicionadas em planos.")
