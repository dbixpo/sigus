# -*- coding: utf-8 -*-
"""Cria tabela empresas_contratadas."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: tabela empresas_contratadas criada (ou já existia).")
