# -*- coding: utf-8 -*-
"""O tema deixa de ser uma cópia da campanha.

O laço é escolhido no cadastro do tipo de ação. Vários temas podem
apontar para a mesma campanha. Cópias automáticas que ninguém usou saem.

    python migrations/soltar_temas_campanha.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text

from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE tipos_acao
            ADD COLUMN IF NOT EXISTS campanha_id INTEGER
            REFERENCES campanhas_saude(id) ON DELETE SET NULL
        """))
        nomes = conn.execute(text("""
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_attribute a
              ON a.attrelid = t.oid AND a.attnum = ANY (c.conkey)
            WHERE t.relname = 'tipos_acao'
              AND c.contype = 'u'
              AND a.attname = 'campanha_id'
        """)).fetchall()
        for (nome,) in nomes:
            conn.execute(text(
                f'ALTER TABLE tipos_acao DROP CONSTRAINT IF EXISTS "{nome}"'
            ))
        apagados = conn.execute(text("""
            DELETE FROM tipos_acao t
            WHERE t.campanha_id IS NOT NULL
              AND t.codigo_esus IS NULL
              AND t.nome = (
                  SELECT c.nome FROM campanhas_saude c WHERE c.id = t.campanha_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM acoes_locais a WHERE a.tipo_acao_id = t.id
              )
        """)).rowcount
    from app.models.noticias import TipoAcao
    ligados = TipoAcao.query.filter(TipoAcao.campanha_id.isnot(None)).count()
    print(f'OK. {apagados} cópia(s) sem uso removida(s). {ligados} tema(s) ainda ligado(s) a campanha.')
