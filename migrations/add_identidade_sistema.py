# -*- coding: utf-8 -*-
"""Cria identidade da instalação e galeria de assets (idempotente)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS identidade_sistema (
                id             INTEGER PRIMARY KEY,
                municipio      VARCHAR(120) NOT NULL,
                uf             VARCHAR(2) NOT NULL,
                secretaria     VARCHAR(200) NOT NULL,
                orgao_curto    VARCHAR(80) NOT NULL,
                nome_sistema   VARCHAR(40) NOT NULL,
                slogan         VARCHAR(200) NOT NULL,
                dominio_email  VARCHAR(120) NOT NULL,
                cidade_padrao  VARCHAR(120) NOT NULL,
                atualizado_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            INSERT INTO identidade_sistema (
                id, municipio, uf, secretaria, orgao_curto,
                nome_sistema, slogan, dominio_email, cidade_padrao
            )
            SELECT
                1,
                'Sorocaba',
                'SP',
                'Secretaria da Saúde de Sorocaba',
                'Saúde Digital',
                'SIGUS',
                'Sistema Integrado de Gestão das Unidades de Saúde',
                'sorocaba.sp.gov.br',
                'Sorocaba'
            WHERE NOT EXISTS (
                SELECT 1 FROM identidade_sistema WHERE id = 1
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sistema_assets (
                id             SERIAL PRIMARY KEY,
                chave          VARCHAR(80) NOT NULL UNIQUE,
                titulo         VARCHAR(150),
                filename       VARCHAR(200) NOT NULL,
                mime           VARCHAR(80),
                nome_original  VARCHAR(255),
                criado_em      TIMESTAMP NOT NULL DEFAULT NOW(),
                atualizado_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.commit()
    print('OK: identidade_sistema (seed Sorocaba) e sistema_assets.')
