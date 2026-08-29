# -*- coding: utf-8 -*-
"""
Migração: adiciona campos da planilha CONTRATOS ATUAL e tag/aba.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS secao VARCHAR(100)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS numero_contrato VARCHAR(50)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS data_assinatura DATE"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS vigencia VARCHAR(100)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS fonte VARCHAR(150)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS valor_inicial NUMERIC(14,2)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS valor_atual NUMERIC(14,2)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS valor_mensal_atual NUMERIC(14,2)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS aditivo_data_pct VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS reajuste_data_base_pct VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS fiscalizacao VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS supressao_data_pct VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS contato_nome_telefone VARCHAR(300)"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS empenhos TEXT"
        ))
        conn.execute(text(
            "ALTER TABLE contratos ADD COLUMN IF NOT EXISTS tag VARCHAR(80)"
        ))
        conn.commit()

    print("OK: Campos da planilha CONTRATOS ATUAL adicionados.")
