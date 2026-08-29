# -*- coding: utf-8 -*-
"""Cria tabelas documentos_transferencia e itens_documento_transferencia."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: Tabelas documentos_transferencia e itens_documento_transferencia criadas (ou já existiam).")
