"""GUT do setor executante (revisão opcional de prioridade)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for col in ('gut_exec_gravidade', 'gut_exec_urgencia', 'gut_exec_tendencia'):
            conn.execute(text(
                f"ALTER TABLE chamados ADD COLUMN IF NOT EXISTS {col} INTEGER"
            ))
        conn.commit()
    print("OK: migração add_chamado_gut_executante concluída.")
