# -*- coding: utf-8 -*-
"""Padrão de ambientes e kit de equipamentos por tipo de sala.

Só cria colunas e a tabela do kit (idempotente). Os dados vêm de
migrations/importar_padrao_salas.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

COMANDOS = [
    "ALTER TABLE tipos_sala ADD COLUMN IF NOT EXISTS codigo VARCHAR(20)",
    "ALTER TABLE tipos_sala ADD COLUMN IF NOT EXISTS grupo VARCHAR(120)",
    "ALTER TABLE tipos_sala ADD COLUMN IF NOT EXISTS ordem INTEGER",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_sala_codigo ON tipos_sala (codigo) WHERE codigo IS NOT NULL",

    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS codigo VARCHAR(20)",
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS classificacao VARCHAR(120)",
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS valor_referencia NUMERIC(12, 2)",
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS natureza_kit VARCHAR(10)",
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS conta_como_id INTEGER "
    "REFERENCES tipos_equipamento(id) ON DELETE SET NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_tipos_equipamento_codigo ON tipos_equipamento (codigo) WHERE codigo IS NOT NULL",

    "ALTER TABLE unidades ADD COLUMN IF NOT EXISTS codigo_imovel VARCHAR(20)",

    """
    CREATE TABLE IF NOT EXISTS kit_padrao_sala (
        id                  SERIAL PRIMARY KEY,
        tipo_sala_id        INTEGER NOT NULL REFERENCES tipos_sala(id) ON DELETE CASCADE,
        tipo_equipamento_id INTEGER NOT NULL REFERENCES tipos_equipamento(id) ON DELETE CASCADE,
        quantidade          INTEGER NOT NULL DEFAULT 1,
        observacao          VARCHAR(300),
        criado_em           TIMESTAMP NOT NULL DEFAULT NOW(),
        atualizado_em       TIMESTAMP NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_kit_padrao_sala UNIQUE (tipo_sala_id, tipo_equipamento_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_kit_padrao_sala_tipo_sala ON kit_padrao_sala (tipo_sala_id)",
]

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for sql in COMANDOS:
            conn.execute(text(sql))
        conn.commit()
    print('OK: padrão de ambientes e kit por tipo de sala.')
