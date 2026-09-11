# -*- coding: utf-8 -*-
"""Feriados municipais + seed 2026 (Decreto nº 30.713/2025)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

DECRETO = 'Decreto nº 30.713/2025'
LINK = (
    'https://leis.org/municipais/sp/sorocaba/lei/decreto/2025/30713/'
    'decreto-n-30713-2025-dispoe-sobre-os-dias-e-horarios-do-ano-de-2026-em-que-'
    'nao-havera-expediente-nas-unidades-dos-orgaos-da-administracao-direta-e-'
    'indireta-do-poder-executivo-do-municipio-de-sorocaba-e-da-outras'
)

# data, nome, tipo, natureza, dia_inteiro, expediente_inicio, expediente_fim, observacao
SEED_2026 = [
    ('2026-01-01', 'Confraternização Universal', 'feriado', 'nacional', True, None, None, 'Ano Novo'),
    ('2026-01-02', 'Confraternização Universal', 'ponto_facultativo', 'municipal', True, None, None, 'Emenda de Ano Novo'),
    ('2026-02-16', 'Carnaval', 'ponto_facultativo', 'municipal', True, None, None, None),
    ('2026-02-17', 'Carnaval', 'ponto_facultativo', 'municipal', True, None, None, None),
    ('2026-02-18', 'Quarta-feira de Cinzas', 'ponto_facultativo', 'municipal', False, '12:00', '17:00',
     'Expediente dos serviços burocráticos a partir das 12h'),
    ('2026-04-02', 'Endoenças', 'ponto_facultativo', 'municipal', True, None, None, None),
    ('2026-04-03', 'Paixão de Cristo', 'feriado', 'nacional', True, None, None, None),
    ('2026-04-20', 'Tiradentes', 'ponto_facultativo', 'municipal', True, None, None, 'Emenda'),
    ('2026-04-21', 'Tiradentes', 'feriado', 'nacional', True, None, None, None),
    ('2026-05-01', 'Dia do Trabalho', 'feriado', 'nacional', True, None, None, None),
    ('2026-06-04', 'Corpus Christi', 'feriado', 'municipal', True, None, None, None),
    ('2026-06-05', 'Corpus Christi', 'ponto_facultativo', 'municipal', True, None, None, 'Emenda'),
    ('2026-07-09', 'Revolução Constitucionalista de 1932', 'feriado', 'estadual', True, None, None, None),
    ('2026-07-10', 'Revolução Constitucionalista de 1932', 'ponto_facultativo', 'municipal', True, None, None, 'Emenda'),
    ('2026-08-15', 'Aniversário de Sorocaba', 'feriado', 'municipal', True, None, None, None),
    ('2026-09-07', 'Independência do Brasil', 'feriado', 'nacional', True, None, None, None),
    ('2026-10-12', 'Nossa Senhora Aparecida', 'feriado', 'nacional', True, None, None, None),
    ('2026-10-30', 'Dia do Funcionário Público', 'ponto_facultativo', 'municipal', True, None, None, None),
    ('2026-11-02', 'Finados', 'feriado', 'nacional', True, None, None, None),
    ('2026-11-15', 'Proclamação da República', 'feriado', 'nacional', True, None, None, None),
    ('2026-11-20', 'Consciência Negra', 'feriado', 'nacional', True, None, None, None),
    ('2026-12-24', 'Véspera de Natal', 'ponto_facultativo', 'municipal', True, None, None, None),
    ('2026-12-25', 'Natal', 'feriado', 'nacional', True, None, None, None),
    ('2026-12-31', 'Véspera de Ano Novo', 'ponto_facultativo', 'municipal', True, None, None, None),
]

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feriados (
                id                 SERIAL PRIMARY KEY,
                data               DATE NOT NULL UNIQUE,
                nome               VARCHAR(200) NOT NULL,
                tipo               VARCHAR(30) NOT NULL DEFAULT 'feriado',
                natureza           VARCHAR(20) NOT NULL DEFAULT 'nacional',
                numero_decreto     VARCHAR(120),
                link_decreto       VARCHAR(500),
                dia_inteiro        BOOLEAN NOT NULL DEFAULT TRUE,
                expediente_inicio  TIME,
                expediente_fim     TIME,
                observacao         VARCHAR(400),
                ativo              BOOLEAN NOT NULL DEFAULT TRUE
            )
        """))
        for row in SEED_2026:
            conn.execute(text("""
                INSERT INTO feriados (
                    data, nome, tipo, natureza, numero_decreto, link_decreto,
                    dia_inteiro, expediente_inicio, expediente_fim, observacao, ativo
                ) VALUES (
                    :data, :nome, :tipo, :natureza, :decreto, :link,
                    :dia_inteiro, CAST(:exp_ini AS TIME), CAST(:exp_fim AS TIME), :obs, TRUE
                )
                ON CONFLICT (data) DO NOTHING
            """), {
                'data': row[0],
                'nome': row[1],
                'tipo': row[2],
                'natureza': row[3],
                'decreto': DECRETO,
                'link': LINK,
                'dia_inteiro': row[4],
                'exp_ini': row[5],
                'exp_fim': row[6],
                'obs': row[7],
            })
        conn.commit()
    print('OK: tabela feriados e seed 2026 (Decreto 30.713/2025).')
