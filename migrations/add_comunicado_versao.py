# -*- coding: utf-8 -*-
"""Versão do comunicado (edição pede nova ciência) e exclusão lógica. Idempotente.

Cada ciência guarda a versão assinada; ao editar, a versão sobe e as ciências
antigas continuam no banco como histórico.
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
            ADD COLUMN IF NOT EXISTS versao INTEGER NOT NULL DEFAULT 1
        """))
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS editado_em TIMESTAMP
        """))
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS editado_por_id INTEGER
                REFERENCES usuarios(id) ON DELETE SET NULL
        """))
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMP
        """))
        conn.execute(text("""
            ALTER TABLE comunicados
            ADD COLUMN IF NOT EXISTS excluido_por_id INTEGER
                REFERENCES usuarios(id) ON DELETE SET NULL
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            ADD COLUMN IF NOT EXISTS versao INTEGER NOT NULL DEFAULT 1
        """))
        conn.execute(text("""
            ALTER TABLE comunicado_ciencias
            DROP CONSTRAINT IF EXISTS uq_comunicado_ciencia
        """))
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_comunicado_ciencia_versao'
                ) THEN
                    ALTER TABLE comunicado_ciencias
                    ADD CONSTRAINT uq_comunicado_ciencia_versao
                    UNIQUE (comunicado_id, usuario_id, versao);
                END IF;
            END $$;
        """))
        conn.commit()
    print('OK: comunicados com versão, edição e exclusão lógica.')
