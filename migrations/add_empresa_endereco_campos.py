# -*- coding: utf-8 -*-
"""
Migração: adiciona campos estruturados de endereço em empresas_contratadas.

- logradouro, numero, complemento, bairro, cidade, estado, cep
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for col, typ in [
            ('logradouro', 'VARCHAR(200)'),
            ('numero', 'VARCHAR(20)'),
            ('complemento', 'VARCHAR(100)'),
            ('bairro', 'VARCHAR(100)'),
            ('cidade', 'VARCHAR(100)'),
            ('estado', 'VARCHAR(2)'),
            ('cep', 'VARCHAR(10)'),
        ]:
            conn.execute(text(
                f"ALTER TABLE empresas_contratadas ADD COLUMN IF NOT EXISTS {col} {typ}"
            ))
        conn.commit()

    print("OK: campos de endereço estruturado adicionados em empresas_contratadas.")
