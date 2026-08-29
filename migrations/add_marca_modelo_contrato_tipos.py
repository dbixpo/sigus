# -*- coding: utf-8 -*-
"""
Migração: adiciona marca_id e modelo_id em contrato_tipos_equipamento.
Permite granularidade: só tipo / tipo+marca / tipo+marca+modelo.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # 1. Adicionar colunas (se não existirem)
        for col in ('marca_id', 'modelo_id'):
            r = conn.execute(text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'contrato_tipos_equipamento' "
                "AND column_name = :col"
            ), {'col': col}).fetchone()
            if not r:
                conn.execute(text(
                    f"ALTER TABLE contrato_tipos_equipamento ADD COLUMN {col} INTEGER "
                    f"REFERENCES {('marcas' if col == 'marca_id' else 'modelos')}(id) ON DELETE CASCADE"
                ))

        # 2. Remover constraint antiga (se existir) e adicionar nova
        try:
            conn.execute(text(
                "ALTER TABLE contrato_tipos_equipamento "
                "DROP CONSTRAINT IF EXISTS contrato_tipos_equipamento_contrato_id_tipo_equipamento_id_key"
            ))
        except Exception:
            pass
        try:
            conn.execute(text(
                "ALTER TABLE contrato_tipos_equipamento "
                "DROP CONSTRAINT IF EXISTS uq_contrato_tipo_marca_modelo"
            ))
        except Exception:
            pass
        try:
            conn.execute(text(
                "ALTER TABLE contrato_tipos_equipamento "
                "ADD CONSTRAINT uq_contrato_tipo_marca_modelo "
                "UNIQUE (contrato_id, tipo_equipamento_id, marca_id, modelo_id)"
            ))
        except Exception as e:
            print(f"Aviso ao criar constraint: {e}")
        conn.commit()

    print("OK: marca_id e modelo_id adicionados em contrato_tipos_equipamento.")
