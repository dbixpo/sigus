# -*- coding: utf-8 -*-
"""Colunas JSON de recorte da ciência (perfil OU CBO). Idempotente.

A lógica de matching (cadastro + matrícula; um recorte ou outro) vive no
código Flask. Este script só garante ciencia_perfis e ciencia_cbos na tabela.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS ciencia_perfis TEXT
        """))
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS ciencia_cbos TEXT
        """))
        conn.commit()
    print('OK: comunicados com filtro de perfil e CBO na ciência.')
