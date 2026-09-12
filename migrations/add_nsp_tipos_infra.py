# -*- coding: utf-8 -*-
"""Tipos de incidente de infraestrutura / sistema / recursos (ICPS-OMS / Anvisa)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db
from app.models.nsp import CATALOGOS_INICIAIS

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for row in CATALOGOS_INICIAIS:
            if row[0] != 'tipo_incidente':
                continue
            grupo, slug, nome, ordem, cor, exige_texto, never_event, encerra, padrao = row
            conn.execute(text("""
                INSERT INTO nsp_catalogos
                    (grupo, slug, nome, ordem, cor, exige_texto, never_event, encerra, padrao)
                VALUES
                    (:grupo, :slug, :nome, :ordem, :cor, :exige_texto, :never_event, :encerra, :padrao)
                ON CONFLICT (grupo, slug) DO UPDATE SET
                    ordem = EXCLUDED.ordem,
                    nome = CASE
                        WHEN nsp_catalogos.slug = 'equipamento'
                             AND nsp_catalogos.nome = 'Falha de equipamento / infraestrutura'
                        THEN EXCLUDED.nome
                        ELSE nsp_catalogos.nome
                    END
            """), {
                'grupo': grupo, 'slug': slug, 'nome': nome, 'ordem': ordem, 'cor': cor,
                'exige_texto': exige_texto, 'never_event': never_event,
                'encerra': encerra, 'padrao': padrao,
            })
        conn.commit()
    print('OK: tipos de incidente de sistema/energia/internet, infraestrutura e recursos.')
