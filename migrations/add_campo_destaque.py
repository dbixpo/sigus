"""Adiciona coluna campo_destaque em campos_tipo_equipamento."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
import sqlalchemy as sa

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        res = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='campos_tipo_equipamento' AND column_name='campo_destaque'"
        )).fetchone()
        if not res:
            conn.execute(sa.text(
                "ALTER TABLE campos_tipo_equipamento "
                "ADD COLUMN campo_destaque BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            conn.commit()
            print("OK: coluna campo_destaque adicionada.")
        else:
            print("OK: coluna ja existia.")
