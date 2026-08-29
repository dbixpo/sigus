import sys
import os
from sqlalchemy import text
from app import create_app, db

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # Adiciona colunas para tipos de CNPJ
        conn.execute(text("""
            ALTER TABLE empresas_contratadas 
            ADD COLUMN IF NOT EXISTS cnpj_estagio BOOLEAN NOT NULL DEFAULT FALSE
        """))
        conn.execute(text("""
            ALTER TABLE empresas_contratadas 
            ADD COLUMN IF NOT EXISTS cnpj_residencia BOOLEAN NOT NULL DEFAULT FALSE
        """))
        conn.execute(text("""
            ALTER TABLE empresas_contratadas 
            ADD COLUMN IF NOT EXISTS cnpj_vinculo_empregaticio_cpd BOOLEAN NOT NULL DEFAULT FALSE
        """))
        conn.commit()
    print("OK: Colunas de tipos de CNPJ adicionadas em empresas_contratadas.")
