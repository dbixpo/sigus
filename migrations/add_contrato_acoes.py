# -*- coding: utf-8 -*-
"""
Migração: cria tabela contrato_acoes para histórico de ações do contrato.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.contrato import ContratoAcao

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: tabela contrato_acoes criada (ou já existia).")
