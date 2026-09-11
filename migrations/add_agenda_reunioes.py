# -*- coding: utf-8 -*-
"""Participantes de reunião na agenda + tipo do evento."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) NOT NULL DEFAULT 'evento'"
        ))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agenda_evento_participantes (
                evento_id  INTEGER NOT NULL REFERENCES agenda_eventos(id) ON DELETE CASCADE,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                PRIMARY KEY (evento_id, usuario_id)
            )
        """))
        conn.commit()
    print('OK: tipo e participantes na agenda.')
