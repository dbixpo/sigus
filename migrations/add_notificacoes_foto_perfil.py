# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.create_all()   # cria tabela notificacoes

    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(200)"
        ))
        conn.commit()

    print("OK: notificacoes e foto_perfil criados.")
