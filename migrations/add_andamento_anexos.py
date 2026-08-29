"""Cria tabela andamento_anexos e adiciona colunas ao chamado_historico."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.create_all()   # cria andamento_anexos se não existir

    cols = [
        ("tipo_andamento",  "VARCHAR(30) NOT NULL DEFAULT 'andamento'"),
        ("requer_resposta", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("respondido_em",   "TIMESTAMP"),
        ("contrato_id",     "INTEGER REFERENCES contratos(id) ON DELETE SET NULL"),
    ]

    with db.engine.connect() as conn:
        for col, typ in cols:
            conn.execute(text(
                f"ALTER TABLE chamado_historico ADD COLUMN IF NOT EXISTS {col} {typ}"
            ))
        conn.commit()

    print("OK: migração andamento_anexos concluída.")
