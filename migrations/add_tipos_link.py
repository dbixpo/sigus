"""Cria tabela tipos_link e adiciona FK tipo_link_id em links_uteis."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # 1. Cria tabela tipos_link (se não existir)
    db.create_all()

    # 2. Adiciona FK na tabela links_uteis
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE links_uteis
            ADD COLUMN IF NOT EXISTS tipo_link_id INTEGER
            REFERENCES tipos_link(id) ON DELETE SET NULL
        """))
        # Remove a coluna legada 'tipo' (link/cabecalho) — agora substituída pela FK
        conn.execute(text("""
            ALTER TABLE links_uteis
            DROP COLUMN IF EXISTS tipo
        """))
        conn.commit()

    print("OK: migração tipos_link concluída.")
