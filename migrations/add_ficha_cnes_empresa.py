# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE ficha_cnes_vinculo ADD COLUMN IF NOT EXISTS cnpj_empresa VARCHAR(20)"
        ))
        conn.execute(text(
            "ALTER TABLE ficha_cnes_vinculo ADD COLUMN IF NOT EXISTS nome_empresa VARCHAR(200)"
        ))
        conn.commit()

    print("OK: cnpj_empresa e nome_empresa adicionados a ficha_cnes_vinculo.")
