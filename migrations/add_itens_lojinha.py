# -*- coding: utf-8 -*-
"""Cria tabela itens_lojinha (Lojinha Interna)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: Tabela itens_lojinha criada (ou já existia).")
