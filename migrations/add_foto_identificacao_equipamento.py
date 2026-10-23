# -*- coding: utf-8 -*-
"""Coluna da foto quadrada usada quando o bem não tem patrimônio nem série."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.session.execute(db.text(
        "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS foto_identificacao VARCHAR(80)"
    ))
    db.session.commit()
    print('ok')
os._exit(0)
