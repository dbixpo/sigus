# -*- coding: utf-8 -*-
"""Cria tabela acoes_plano_obs_anexos para anexos nas observações."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acoes_plano_obs_anexos (
                id SERIAL PRIMARY KEY,
                observacao_id INTEGER NOT NULL REFERENCES acoes_plano_observacoes(id) ON DELETE CASCADE,
                filename VARCHAR(200) NOT NULL,
                original VARCHAR(200) NOT NULL,
                mime_type VARCHAR(100)
            )
        """))
        conn.commit()
    print("OK: Tabela acoes_plano_obs_anexos criada.")
