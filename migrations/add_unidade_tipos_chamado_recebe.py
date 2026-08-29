"""Adiciona tipos_chamado_recebe em unidades (fila de gestão por unidade)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE unidades ADD COLUMN IF NOT EXISTS tipos_chamado_recebe JSONB DEFAULT '[]'::jsonb"
        ))
        conn.commit()

    print("OK: migração add_unidade_tipos_chamado_recebe concluída.")
