"""Aumenta tamanho da coluna tipo_chamado para suportar 'solicitacao_equipamento' (23 chars)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE chamados ALTER COLUMN tipo_chamado TYPE VARCHAR(30)"
        ))
        conn.commit()
    print("OK: migração aumentar_tipo_chamado concluída.")
