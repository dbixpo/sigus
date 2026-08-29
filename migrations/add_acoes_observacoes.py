# -*- coding: utf-8 -*-
"""Cria tabela acoes_plano_observacoes para registrar observações nas ações."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acoes_plano_observacoes (
                id SERIAL PRIMARY KEY,
                acao_id INTEGER NOT NULL REFERENCES acoes_plano(id) ON DELETE CASCADE,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                texto TEXT NOT NULL,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    print("OK: Tabela acoes_plano_observacoes criada.")
