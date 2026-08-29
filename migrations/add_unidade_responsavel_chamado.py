"""Adiciona unidade_responsavel_id em chamados."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE chamados ADD COLUMN IF NOT EXISTS unidade_responsavel_id INTEGER "
            "REFERENCES unidades(id) ON DELETE SET NULL"
        ))
        conn.commit()
    print("OK: migração add_unidade_responsavel_chamado concluída.")
