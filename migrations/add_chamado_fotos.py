"""Cria tabela chamado_fotos e adiciona colunas bp_* em chamados."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.create_all()   # cria chamado_fotos se não existir

    cols = [
        ("bp_num_patrimonio",    "VARCHAR(60)"),
        ("bp_nome_equip",        "VARCHAR(200)"),
        ("bp_fabricante_modelo", "VARCHAR(200)"),
        ("bp_num_serie",         "VARCHAR(100)"),
        ("bp_categoria",         "VARCHAR(30)"),
        ("bp_servico",           "VARCHAR(20)"),
        ("bp_problema_em",       "VARCHAR(20)"),
        ("bp_rechamado",         "BOOLEAN DEFAULT FALSE"),
        ("bp_data_rechamado",    "DATE"),
    ]

    with db.engine.connect() as conn:
        for col, typ in cols:
            conn.execute(text(
                f"ALTER TABLE chamados ADD COLUMN IF NOT EXISTS {col} {typ}"
            ))
        conn.commit()

    print("OK: migração chamado_fotos concluída.")
