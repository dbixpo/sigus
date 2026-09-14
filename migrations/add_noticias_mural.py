# -*- coding: utf-8 -*-
"""Cria comunicados, ciência, mural de ações e tipos de ação (idempotente).

Seed inicial: temas para saúde da Ficha de Atividade Coletiva e-SUS APS.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

TEMAS_ESUS = [
    (1, 'Alimentação saudável'),
    (32, 'Alimentação complementar saudável'),
    (31, 'Amamentação'),
    (19, 'Agravos e doenças negligenciadas'),
    (29, 'Ações de combate ao Aedes aegypti'),
    (4, 'Autocuidado de pessoas com doenças crônicas'),
    (5, 'Cidadania e direitos humanos'),
    (8, 'Envelhecimento / climatério / andropausa'),
    (21, 'Outros'),
    (10, 'Plantas medicinais / fitoterapia'),
    (7, 'Prevenção ao uso de álcool, tabaco e outras drogas'),
    (13, 'Prevenção da violência e cultura da paz'),
    (14, 'Saúde ambiental'),
    (15, 'Saúde bucal'),
    (6, 'Saúde do trabalhador'),
    (16, 'Saúde mental'),
    (17, 'Saúde sexual e reprodutiva'),
    (18, 'Semana saúde na escola'),
]

_UPLOADS = [
    os.path.join('app', 'static', 'uploads', 'comunicados'),
    os.path.join('app', 'static', 'uploads', 'acoes'),
]

app = create_app()
with app.app_context():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in _UPLOADS:
        os.makedirs(os.path.join(raiz, rel), exist_ok=True)

    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tipos_acao (
                id            SERIAL PRIMARY KEY,
                nome          VARCHAR(200) NOT NULL UNIQUE,
                codigo_esus   INTEGER,
                descricao     TEXT,
                ativo         BOOLEAN NOT NULL DEFAULT TRUE,
                ordem         INTEGER NOT NULL DEFAULT 0,
                criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
                atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comunicados (
                id                 SERIAL PRIMARY KEY,
                titulo             VARCHAR(200) NOT NULL,
                texto              TEXT,
                autor_id           INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                unidade_origem_id  INTEGER REFERENCES unidades(id) ON DELETE SET NULL,
                exige_ciencia      BOOLEAN NOT NULL DEFAULT TRUE,
                ativo              BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em          TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comunicado_unidades (
                comunicado_id INTEGER NOT NULL REFERENCES comunicados(id) ON DELETE CASCADE,
                unidade_id    INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
                PRIMARY KEY (comunicado_id, unidade_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comunicado_anexos (
                id             SERIAL PRIMARY KEY,
                comunicado_id  INTEGER NOT NULL REFERENCES comunicados(id) ON DELETE CASCADE,
                filename       VARCHAR(200) NOT NULL,
                original       VARCHAR(255),
                mime_type      VARCHAR(80),
                tamanho_bytes  INTEGER,
                criado_em      TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comunicado_ciencias (
                id             SERIAL PRIMARY KEY,
                comunicado_id  INTEGER NOT NULL REFERENCES comunicados(id) ON DELETE CASCADE,
                usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                ciencia_em     TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_comunicado_ciencia UNIQUE (comunicado_id, usuario_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acoes_locais (
                id            SERIAL PRIMARY KEY,
                unidade_id    INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
                autor_id      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                tipo_acao_id  INTEGER REFERENCES tipos_acao(id) ON DELETE SET NULL,
                descricao     VARCHAR(400) NOT NULL,
                data_acao     DATE NOT NULL,
                criado_em     TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS acao_local_fotos (
                id         SERIAL PRIMARY KEY,
                acao_id    INTEGER NOT NULL REFERENCES acoes_locais(id) ON DELETE CASCADE,
                filename   VARCHAR(200) NOT NULL,
                original   VARCHAR(255),
                mime_type  VARCHAR(80),
                ordem      INTEGER NOT NULL DEFAULT 0,
                criado_em  TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            ALTER TABLE notificacoes
            ADD COLUMN IF NOT EXISTS comunicado_id INTEGER
            REFERENCES comunicados(id) ON DELETE CASCADE
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_acoes_locais_criado_em
            ON acoes_locais (criado_em DESC)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_comunicados_criado_em
            ON comunicados (criado_em DESC)
        """))

        for ordem, (codigo, nome) in enumerate(TEMAS_ESUS, start=1):
            conn.execute(text("""
                INSERT INTO tipos_acao (nome, codigo_esus, ativo, ordem)
                SELECT :nome, :codigo, TRUE, :ordem
                WHERE NOT EXISTS (
                    SELECT 1 FROM tipos_acao WHERE nome = :nome
                )
            """), {'nome': nome, 'codigo': codigo, 'ordem': ordem})

        conn.commit()
    print('OK: comunicados, ciências, mural de ações e tipos de ação (seed e-SUS APS).')
