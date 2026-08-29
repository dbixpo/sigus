# -*- coding: utf-8 -*-
"""
Migração: adiciona campos latitude/longitude em predios e unidades.

Uso:
  python migrations/add_lat_lng_predios_unidades.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for tabela in ["predios", "unidades"]:
            conn.execute(text(
                f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION"
            ))
            conn.execute(text(
                f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION"
            ))
        conn.commit()

    print("OK: campos latitude/longitude adicionados em predios e unidades.")

