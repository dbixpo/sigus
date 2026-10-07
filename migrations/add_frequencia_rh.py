# -*- coding: utf-8 -*-
"""Frequência mensal do RH: de-para de locais, base de servidores, função→CBO,
importações, apontamentos por matrícula e horas extras."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db
from app.models.frequencia import (
    RhLocal, RhServidor, RhFuncaoCbo, FreqImportacao, FreqLancamento, FreqHoraExtra,
)

app = create_app()
with app.app_context():
    for modelo in (RhLocal, RhServidor, RhFuncaoCbo, FreqImportacao, FreqLancamento, FreqHoraExtra):
        modelo.__table__.create(bind=db.engine, checkfirst=True)
    with db.engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_freq_importacoes_comp_local "
            "ON freq_importacoes (competencia, local, status)"
        ))
        conn.commit()
    print('OK: tabelas da frequência do RH.')
