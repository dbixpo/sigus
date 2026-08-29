# -*- coding: utf-8 -*-
"""
Migração: cria contrato_tipos_equipamento, adiciona periodo_meses em contrato_acoes.
- contrato_tipos_equipamento: substitui contrato_equipamentos (vincula tipo, não equipamento)
- periodo_meses: para prorrogações (em vez de periodo_dias)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.contrato import ContratoTipoEquipamento
from sqlalchemy import text

app = create_app()
with app.app_context():
    # 1. Criar tabela contrato_tipos_equipamento
    db.create_all()

    # 2. Adicionar periodo_meses em contrato_acoes (PostgreSQL)
    with db.engine.connect() as conn:
        r = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'contrato_acoes' AND column_name = 'periodo_meses'"
        )).fetchone()
        if not r:
            conn.execute(text("ALTER TABLE contrato_acoes ADD COLUMN periodo_meses INTEGER"))
        conn.commit()

    print("OK: contrato_tipos_equipamento e periodo_meses.")
