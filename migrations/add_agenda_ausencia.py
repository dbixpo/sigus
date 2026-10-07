# -*- coding: utf-8 -*-
"""Ausência / férias na agenda: motivo do evento do tipo 'ausencia'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS motivo VARCHAR(20)"
        ))
        conn.commit()
    print('OK: motivo da ausência na agenda.')
