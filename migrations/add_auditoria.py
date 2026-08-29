# -*- coding: utf-8 -*-
"""
Migração: cria tabela auditoria para registro de requisições HTTP.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                acao VARCHAR(50),
                modulo VARCHAR(80),
                endpoint VARCHAR(200),
                url VARCHAR(500),
                method VARCHAR(10),
                parametros JSONB,
                entity_type VARCHAR(80),
                entity_id INTEGER,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                response_status INTEGER,
                detalhes TEXT
            )
        """))
        conn.commit()

    print("OK: Tabela auditoria criada.")
