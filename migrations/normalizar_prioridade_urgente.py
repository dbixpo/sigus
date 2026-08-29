"""Unifica prioridade legada 'urgente' → 'alta' (3 níveis GUT)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        r = conn.execute(text(
            "UPDATE chamados SET prioridade = 'alta' WHERE prioridade = 'urgente'"
        ))
        conn.commit()
    print(f"OK: {r.rowcount} chamado(s) com prioridade 'urgente' migrados para 'alta'.")
