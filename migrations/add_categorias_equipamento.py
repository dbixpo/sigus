# -*- coding: utf-8 -*-
"""Cadastro de categorias de equipamento e vínculo com os tipos já classificados."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db
from app.models.equipamento import CategoriaEquipamento, TipoEquipamento

PADRAO = (
    (1, 'Médico-Assistencial'),
    (2, 'Apoio'),
    (3, 'Infraestrutura'),
    (4, 'Geral'),
)

COMANDOS = [
    """
    CREATE TABLE IF NOT EXISTS categorias_equipamento (
        id            SERIAL PRIMARY KEY,
        nome          VARCHAR(120) NOT NULL,
        descricao     TEXT,
        ordem         INTEGER NOT NULL DEFAULT 0,
        ativo         BOOLEAN NOT NULL DEFAULT TRUE,
        criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
        atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_categorias_equipamento_nome "
    "ON categorias_equipamento (lower(nome))",
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS categoria_id INTEGER "
    "REFERENCES categorias_equipamento(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_tipos_equipamento_categoria ON tipos_equipamento (categoria_id)",
]


def _garantir(nome, ordem):
    categoria = CategoriaEquipamento.query.filter(
        db.func.lower(CategoriaEquipamento.nome) == nome.lower()
    ).first()
    if categoria:
        return categoria
    categoria = CategoriaEquipamento(nome=nome, ordem=ordem, ativo=True)
    db.session.add(categoria)
    db.session.flush()
    return categoria


app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for sql in COMANDOS:
            conn.execute(text(sql))
        conn.commit()
    for ordem, nome in PADRAO:
        _garantir(nome, ordem)
    proxima = 10
    nomes = [
        nome for (nome,) in db.session.query(TipoEquipamento.classificacao)
        .filter(TipoEquipamento.classificacao.isnot(None), TipoEquipamento.classificacao != '')
        .distinct().all()
    ]
    for nome in sorted(nomes, key=str.lower):
        if CategoriaEquipamento.query.filter(db.func.lower(CategoriaEquipamento.nome) == nome.lower()).first():
            continue
        _garantir(nome, proxima)
        proxima += 1
    for tipo in TipoEquipamento.query.filter(TipoEquipamento.classificacao.isnot(None)).all():
        categoria = CategoriaEquipamento.query.filter(
            db.func.lower(CategoriaEquipamento.nome) == tipo.classificacao.lower()
        ).first()
        if categoria:
            tipo.categoria_id = categoria.id
            tipo.classificacao = categoria.nome
    db.session.commit()
    print('OK: categorias de equipamento.', CategoriaEquipamento.query.count())
