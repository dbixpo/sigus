# -*- coding: utf-8 -*-
"""
Migração: adiciona campo de capacidade máxima na tabela salas.

- cria coluna capacidade_maxima (INTEGER, NOT NULL, DEFAULT 0)
- faz backfill para registros existentes

Execute UMA VEZ após atualizar o código.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text

from app import create_app, db


def _column_exists(conn, table_name: str, column_name: str, schema: str | None = None) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        return bool(
            conn.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :table
                      AND column_name = :column
                    LIMIT 1
                    """
                ),
                {"schema": schema or "public", "table": table_name, "column": column_name},
            ).scalar()
        )
    if dialect == "mysql":
        return bool(
            conn.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = :table
                      AND column_name = :column
                    LIMIT 1
                    """
                ),
                {"table": table_name, "column": column_name},
            ).scalar()
        )
    if dialect == "sqlite":
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return any(r[1] == column_name for r in rows)  # r[1] = name
    # fallback genérico: tenta e deixa o ALTER lidar com erro (não ideal, mas evita travar)
    return False


app = create_app()
with app.app_context():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        if not _column_exists(conn, "salas", "capacidade_maxima"):
            # Compatível com PostgreSQL / MySQL / SQLite (versões atuais)
            conn.execute(
                text(
                    "ALTER TABLE salas ADD COLUMN capacidade_maxima INTEGER NOT NULL DEFAULT 0"
                )
            )
        # Backfill (garantia)
        conn.execute(text("UPDATE salas SET capacidade_maxima = 0 WHERE capacidade_maxima IS NULL"))
        trans.commit()
        print("OK: coluna salas.capacidade_maxima criada/ajustada.")
    except Exception as e:
        trans.rollback()
        print(f"ERRO: {e}")
        raise
    finally:
        conn.close()

