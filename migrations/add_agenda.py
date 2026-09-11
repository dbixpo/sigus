# -*- coding: utf-8 -*-
"""Cria a agenda da unidade e libera a permissão a partir de Planejamentos."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agenda_eventos (
                id            SERIAL PRIMARY KEY,
                unidade_id    INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
                titulo        VARCHAR(200) NOT NULL,
                descricao     TEXT,
                local         VARCHAR(300),
                inicio        TIMESTAMP NOT NULL,
                fim           TIMESTAMP,
                dia_inteiro   BOOLEAN NOT NULL DEFAULT FALSE,
                visibilidade  VARCHAR(20) NOT NULL DEFAULT 'unidade',
                criado_por    INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
                atualizado_em TIMESTAMP
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_agenda_eventos_unidade_inicio "
            "ON agenda_eventos (unidade_id, inicio)"
        ))
        conn.execute(text("""
            INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
            SELECT perfil, 'Agenda', ver, editar, adicionar
            FROM perfil_permissoes
            WHERE secao = 'Planejamentos'
            ON CONFLICT (perfil, secao) DO NOTHING
        """))
        conn.commit()
    print('OK: tabela agenda_eventos e permissao Agenda.')
