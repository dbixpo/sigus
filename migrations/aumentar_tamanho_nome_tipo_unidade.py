import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE tipos_unidade ALTER COLUMN nome TYPE VARCHAR(200)"))
        conn.commit()
    print("OK: Campo nome em tipos_unidade agora aceita até 200 caracteres.")
