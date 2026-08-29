# -*- coding: utf-8 -*-
"""Adiciona dt_entrada_pais e pais_origem à tabela solicitacoes_vinculo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE solicitacoes_vinculo ADD COLUMN IF NOT EXISTS dt_entrada_pais DATE"
        ))
        conn.execute(text(
            "ALTER TABLE solicitacoes_vinculo ADD COLUMN IF NOT EXISTS pais_origem VARCHAR(100)"
        ))
        conn.commit()

    print("OK: dt_entrada_pais e pais_origem adicionados a solicitacoes_vinculo.")
