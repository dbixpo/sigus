"""Campos para abertura externa de chamados (sem login)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE chamados ADD COLUMN IF NOT EXISTS externo_nome VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE chamados ADD COLUMN IF NOT EXISTS externo_whatsapp VARCHAR(20)"
        ))
        conn.execute(text(
            "ALTER TABLE chamados ALTER COLUMN aberto_por DROP NOT NULL"
        ))
        conn.commit()
    print("OK: migração add_chamado_externo concluída.")
