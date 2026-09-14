# -*- coding: utf-8 -*-
"""Curtidas e comentários no mural de ações (idempotente)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acao_local_curtidas (
                id         SERIAL PRIMARY KEY,
                acao_id    INTEGER NOT NULL REFERENCES acoes_locais(id) ON DELETE CASCADE,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                criado_em  TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_acao_curtida UNIQUE (acao_id, usuario_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acao_local_comentarios (
                id         SERIAL PRIMARY KEY,
                acao_id    INTEGER NOT NULL REFERENCES acoes_locais(id) ON DELETE CASCADE,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                texto      VARCHAR(280) NOT NULL,
                criado_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_acao_curtidas_acao
            ON acao_local_curtidas (acao_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_acao_comentarios_acao
            ON acao_local_comentarios (acao_id, criado_em)
        """))
        conn.commit()
    print('OK: mural com curtidas e comentários.')
