# -*- coding: utf-8 -*-
"""Cria tabelas planos e acoes_plano (Kanban + GUT)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS planos (
                id SERIAL PRIMARY KEY,
                unidade_id INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
                titulo VARCHAR(200) NOT NULL,
                descricao TEXT,
                gravidade INTEGER NOT NULL DEFAULT 1,
                urgencia INTEGER NOT NULL DEFAULT 1,
                tendencia INTEGER NOT NULL DEFAULT 1,
                criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acoes_plano (
                id SERIAL PRIMARY KEY,
                plano_id INTEGER NOT NULL REFERENCES planos(id) ON DELETE CASCADE,
                titulo VARCHAR(300) NOT NULL,
                descricao TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'backlog',
                ordem INTEGER NOT NULL DEFAULT 0,
                criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acacao_responsaveis (
                acao_id INTEGER NOT NULL REFERENCES acoes_plano(id) ON DELETE CASCADE,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                PRIMARY KEY (acao_id, usuario_id)
            )
        """))
        conn.commit()
    print("OK: Tabelas planos, acoes_plano e acacao_responsaveis criadas.")
