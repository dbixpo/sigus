# -*- coding: utf-8 -*-
"""
Migração: cria tabela contrato_financeiro (empenhos, fontes e notas).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contrato_financeiro (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(50),
                processo VARCHAR(100),
                motivo VARCHAR(80),
                prestador VARCHAR(200),
                objeto TEXT,
                referencia VARCHAR(150),
                valor_total NUMERIC(14,2),
                especializada VARCHAR(100),
                vigilancia VARCHAR(100),
                atencao_basica VARCHAR(100),
                outros VARCHAR(100),
                tabela_sus VARCHAR(100),
                complemento VARCHAR(150),
                emenda_municipal VARCHAR(100),
                emenda_estadual VARCHAR(100),
                emenda_federal VARCHAR(100),
                observacao TEXT,
                data_necessaria DATE,
                data_envio_divisao DATE,
                data_envio_fms DATE,
                data_devolucao_setor DATE,
                reservas VARCHAR(200),
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

    print("OK: Tabela contrato_financeiro criada.")
