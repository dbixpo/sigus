# -*- coding: utf-8 -*-
"""
Migração: adiciona campos de blocos em empresas_contratadas e vincula contratos.

- empresas_contratadas: endereco, email_suporte, telefone_suporte
- contratos: empresa_id (FK para empresas_contratadas)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # empresas_contratadas
        conn.execute(text(
            "ALTER TABLE empresas_contratadas ADD COLUMN IF NOT EXISTS endereco TEXT"
        ))
        conn.execute(text(
            "ALTER TABLE empresas_contratadas ADD COLUMN IF NOT EXISTS email_suporte VARCHAR(150)"
        ))
        conn.execute(text(
            "ALTER TABLE empresas_contratadas ADD COLUMN IF NOT EXISTS telefone_suporte VARCHAR(30)"
        ))
        # contratos
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas_contratadas(id) ON DELETE SET NULL"
        ))
        try:
            conn.execute(text(
                "ALTER TABLE contratos ALTER COLUMN empresa DROP NOT NULL"
            ))
        except Exception:
            pass  # SQLite não suporta ALTER COLUMN; PostgreSQL sim
        conn.commit()

    print("OK: blocos empresa e vínculo contrato-empresa aplicados.")
