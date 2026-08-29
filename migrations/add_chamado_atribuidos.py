"""Tabela chamado_atribuidos — múltiplos responsáveis por chamado."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chamado_atribuidos (
                id SERIAL PRIMARY KEY,
                chamado_id INTEGER NOT NULL REFERENCES chamados(id) ON DELETE CASCADE,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                atribuido_em TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (chamado_id, usuario_id)
            )
        """))
        conn.commit()
    print("OK: migração add_chamado_atribuidos concluída.")
