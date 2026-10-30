# -*- coding: utf-8 -*-
"""Tabelas do Metabase incorporado e o painel 580 (idempotente).

A chave secreta NÃO fica neste arquivo. Ela entra só se METABASE_SECRET_KEY
estiver no ambiente (.env desta máquina) e a linha do banco ainda estiver vazia.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

SITE_PADRAO = 'https://saudedigital.sorocaba.sp.gov.br/metabase'

app = create_app()
with app.app_context():
    site = (os.environ.get('METABASE_SITE_URL') or SITE_PADRAO).strip().rstrip('/')
    chave = (os.environ.get('METABASE_SECRET_KEY') or '').strip()
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metabase_config (
                id                  INTEGER PRIMARY KEY,
                site_url            VARCHAR(300) NOT NULL DEFAULT '',
                secret_key          VARCHAR(200) NOT NULL DEFAULT '',
                intervalo_segundos  INTEGER NOT NULL DEFAULT 40,
                atualizado_em       TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metabase_paineis (
                id                 SERIAL PRIMARY KEY,
                nome               VARCHAR(150) NOT NULL,
                descricao          VARCHAR(300),
                resource_id        INTEGER NOT NULL,
                bordered           BOOLEAN NOT NULL DEFAULT TRUE,
                titled             BOOLEAN NOT NULL DEFAULT TRUE,
                ativo              BOOLEAN NOT NULL DEFAULT TRUE,
                ordem              INTEGER NOT NULL DEFAULT 0,
                perfis_acesso      JSON NOT NULL DEFAULT '["todos"]',
                tipos_unidade_ids  JSON NOT NULL DEFAULT '[]',
                cbos               JSON NOT NULL DEFAULT '[]',
                criado_por         INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em          TIMESTAMP NOT NULL DEFAULT NOW(),
                atualizado_em      TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            INSERT INTO metabase_config (id, site_url, secret_key, intervalo_segundos)
            SELECT 1, :site, :chave, 40
            WHERE NOT EXISTS (SELECT 1 FROM metabase_config WHERE id = 1)
        """), {'site': site, 'chave': chave})
        if chave:
            conn.execute(text("""
                UPDATE metabase_config
                   SET secret_key = :chave
                 WHERE id = 1
                   AND (secret_key IS NULL OR secret_key = '')
            """), {'chave': chave})
        conn.execute(text("""
            UPDATE metabase_config
               SET site_url = :site
             WHERE id = 1
               AND (site_url IS NULL OR site_url = '')
        """), {'site': site})
        conn.execute(text("""
            UPDATE metabase_config
               SET site_url = 'https://saudedigital.sorocaba.sp.gov.br/metabase'
             WHERE id = 1
               AND site_url = 'http://saudedigital.sorocaba.sp.gov.br/metabase'
        """))
        conn.execute(text("""
            ALTER TABLE metabase_paineis
                ADD COLUMN IF NOT EXISTS with_downloads BOOLEAN NOT NULL DEFAULT TRUE
        """))
        conn.execute(text("""
            ALTER TABLE metabase_paineis
                ADD COLUMN IF NOT EXISTS embedding_params JSON NOT NULL DEFAULT CAST('{}' AS json)
        """))
        conn.execute(text("""
            ALTER TABLE metabase_paineis
                ADD COLUMN IF NOT EXISTS initial_parameters JSON NOT NULL DEFAULT CAST('{}' AS json)
        """))
        conn.execute(text("""
            ALTER TABLE metabase_paineis
                ADD COLUMN IF NOT EXISTS params JSON NOT NULL DEFAULT CAST('{}' AS json)
        """))
        conn.execute(text("""
            UPDATE metabase_paineis
               SET embedding_params = CAST('{}' AS json),
                   initial_parameters = CAST('{}' AS json)
             WHERE resource_id = 580
               AND CAST(embedding_params AS text) LIKE '%data_da_aplica%'
        """))
        conn.execute(text("""
            ALTER TABLE metabase_paineis
                ALTER COLUMN with_downloads SET DEFAULT FALSE
        """))
        conn.execute(text("""
            UPDATE metabase_paineis
               SET with_downloads = FALSE
        """))
        conn.execute(text("""
            INSERT INTO metabase_paineis (
                nome, descricao, resource_id, bordered, titled, ativo, ordem,
                perfis_acesso, tipos_unidade_ids, cbos
            )
            SELECT
                'Painel 580',
                'Dashboard incorporado do Metabase.',
                580,
                TRUE,
                TRUE,
                TRUE,
                0,
                CAST('["todos"]' AS json),
                CAST('[]' AS json),
                CAST('[]' AS json)
            WHERE NOT EXISTS (
                SELECT 1 FROM metabase_paineis WHERE resource_id = 580
            )
        """))
        conn.commit()
    print('OK: metabase_config, metabase_paineis e o dashboard 580 (se ainda não existia).')
    if not chave:
        print('AVISO: METABASE_SECRET_KEY vazia. Cole a chave em Configurações → Metabase.')
