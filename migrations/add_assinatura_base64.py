# -*- coding: utf-8 -*-
"""Adiciona coluna assinatura_base64 à tabela solicitacoes_vinculo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE solicitacoes_vinculo ADD COLUMN IF NOT EXISTS assinatura_base64 TEXT"
        ))
        conn.commit()

    print("OK: coluna assinatura_base64 adicionada à tabela solicitacoes_vinculo.")
