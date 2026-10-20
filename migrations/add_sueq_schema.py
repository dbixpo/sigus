# -*- coding: utf-8 -*-
"""Cria schema PostgreSQL sueq, tabelas SUEQ e permissões OP_*."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db
from app.models.sueq import (
    SueqParlamentar, SueqUnidade, SueqProcesso, SueqEmenda, SueqEmendaItem,
    SueqChamado, SueqChamadoControle,
)

SECOES_SUEQ = ('OP_Emendas', 'OP_Licitacoes', 'OP_ChamadosSueq')

app = create_app()
with app.app_context():
    with db.engine.begin() as conn:
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS sueq'))

    # Ordem respeita FKs internas do schema
    for model in (
        SueqParlamentar, SueqUnidade, SueqProcesso, SueqEmenda,
        SueqEmendaItem, SueqChamado, SueqChamadoControle,
    ):
        model.__table__.create(db.engine, checkfirst=True)

    with db.engine.begin() as conn:
        # Admin: acesso total às três seções SUEQ
        for secao in SECOES_SUEQ:
            conn.execute(text("""
                INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
                VALUES ('administrador', :secao, TRUE, TRUE, TRUE)
                ON CONFLICT (perfil, secao) DO NOTHING
            """), {'secao': secao})

        # Demais perfis: herdam o mesmo padrão de OP_Contratos (se existir)
        for secao in SECOES_SUEQ:
            conn.execute(text("""
                INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
                SELECT perfil, :secao, ver, editar, adicionar
                FROM perfil_permissoes
                WHERE secao = 'OP_Contratos'
                  AND perfil <> 'administrador'
                ON CONFLICT (perfil, secao) DO NOTHING
            """), {'secao': secao})

    with db.engine.connect() as conn:
        tabelas = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'sueq' ORDER BY table_name
        """)).fetchall()
        perms = conn.execute(text("""
            SELECT perfil, secao, ver, editar, adicionar
            FROM perfil_permissoes
            WHERE secao = ANY(:secoes)
            ORDER BY secao, perfil
        """), {'secoes': list(SECOES_SUEQ)}).fetchall()

    print('OK: schema sueq + tabelas:', ', '.join(t[0] for t in tabelas))
    print('OK: permissoes SUEQ:', len(perms), 'linhas')
