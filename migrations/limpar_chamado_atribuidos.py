"""Remove atribuições de chamados (feature descontinuada)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        r1 = conn.execute(text("DELETE FROM chamado_atribuidos"))
        r2 = conn.execute(text(
            "UPDATE chamados SET responsavel_id = NULL WHERE responsavel_id IS NOT NULL"
        ))
        conn.commit()
    print(f"OK: {r1.rowcount} atribuição(ões) removida(s); "
          f"{r2.rowcount} responsavel_id limpo(s).")
