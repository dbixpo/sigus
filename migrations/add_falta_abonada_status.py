# -*- coding: utf-8 -*-
"""Adiciona colunas de status/cancelamento à tabela faltas_abonadas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE faltas_abonadas ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ativa'"
        ))
        conn.execute(text(
            "ALTER TABLE faltas_abonadas ADD COLUMN IF NOT EXISTS motivo_cancelamento TEXT"
        ))
        conn.execute(text(
            "ALTER TABLE faltas_abonadas ADD COLUMN IF NOT EXISTS cancelado_em TIMESTAMP"
        ))
        conn.execute(text(
            "ALTER TABLE faltas_abonadas ADD COLUMN IF NOT EXISTS cancelado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL"
        ))
        conn.commit()

    print("OK: colunas de cancelamento adicionadas a faltas_abonadas.")
