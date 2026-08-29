# -*- coding: utf-8 -*-
"""Migração: cria tabela acacao_empresas (ação ↔ empresa contratada)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: acacao_empresas criada (ou já existia).")
