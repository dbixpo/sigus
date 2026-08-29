"""Adiciona coluna imagem_path em links_uteis."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE links_uteis ADD COLUMN IF NOT EXISTS imagem_path VARCHAR(300)"
        ))
        conn.commit()
    print("OK: coluna imagem_path adicionada (ou ja existia).")
