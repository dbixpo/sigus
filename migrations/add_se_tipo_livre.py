"""Adiciona se_tipo_livre em chamados para 'Tipo não listado'."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE chamados ADD COLUMN IF NOT EXISTS se_tipo_livre VARCHAR(150)"
        ))
        conn.commit()
    print("OK: migração add_se_tipo_livre concluída.")
