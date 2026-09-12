# -*- coding: utf-8 -*-
"""CPF/CNS na ocorrência NSP e nomes em português nos catálogos."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE nsp_ocorrencias ADD COLUMN IF NOT EXISTS cpf VARCHAR(14)"
        ))
        conn.execute(text(
            "ALTER TABLE nsp_ocorrencias ADD COLUMN IF NOT EXISTS cns VARCHAR(20)"
        ))
        conn.execute(text("""
            UPDATE nsp_catalogos
            SET nome = 'Quase erro'
            WHERE grupo = 'classificacao' AND slug = 'near_miss'
              AND nome ILIKE '%near miss%'
        """))
        conn.commit()
    print('OK: colunas cpf/cns e rótulo Quase erro.')
