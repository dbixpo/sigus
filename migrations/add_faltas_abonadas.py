# -*- coding: utf-8 -*-
"""Cria a tabela faltas_abonadas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS faltas_abonadas (
                id          SERIAL PRIMARY KEY,
                usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                unidade_id  INTEGER REFERENCES unidades(id) ON DELETE SET NULL,
                data_falta  DATE NOT NULL,
                funcao      VARCHAR(200) NOT NULL,
                criado_em   TIMESTAMP NOT NULL DEFAULT NOW(),
                criado_por  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_faltas_abonadas_usuario_id ON faltas_abonadas (usuario_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_faltas_abonadas_data ON faltas_abonadas (data_falta)"
        ))
        conn.commit()

    print("OK: tabela faltas_abonadas criada.")
