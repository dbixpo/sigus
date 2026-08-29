"""Adiciona campos GUT para chamados de Solicitação Administrativa."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for col in ('sa_gravidade', 'sa_urgencia', 'sa_tendencia'):
            conn.execute(text(
                f"ALTER TABLE chamados ADD COLUMN IF NOT EXISTS {col} INTEGER"
            ))
        conn.commit()

    print("OK: migração add_solicitacao_administrativa concluída.")
