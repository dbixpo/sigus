# -*- coding: utf-8 -*-
"""Adiciona tabelas de relacionamento many-to-many para unidades e tipos de unidades em planejamentos."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Criando tabelas de relacionamento many-to-many para planejamentos...")
    
    # Cria tabela planejamento_unidades
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS planejamento_unidades (
            planejamento_id INTEGER NOT NULL,
            unidade_id INTEGER NOT NULL,
            PRIMARY KEY (planejamento_id, unidade_id),
            FOREIGN KEY (planejamento_id) REFERENCES planejamentos(id) ON DELETE CASCADE,
            FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE
        )
    """))
    
    # Cria tabela planejamento_tipos_unidade
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS planejamento_tipos_unidade (
            planejamento_id INTEGER NOT NULL,
            tipo_unidade_id INTEGER NOT NULL,
            PRIMARY KEY (planejamento_id, tipo_unidade_id),
            FOREIGN KEY (planejamento_id) REFERENCES planejamentos(id) ON DELETE CASCADE,
            FOREIGN KEY (tipo_unidade_id) REFERENCES tipos_unidade(id) ON DELETE CASCADE
        )
    """))
    
    # Migra dados existentes: adiciona unidade_id atual à tabela planejamento_unidades
    db.session.execute(text("""
        INSERT INTO planejamento_unidades (planejamento_id, unidade_id)
        SELECT id, unidade_id
        FROM planejamentos
        WHERE NOT EXISTS (
            SELECT 1 FROM planejamento_unidades pu
            WHERE pu.planejamento_id = planejamentos.id
        )
    """))
    
    db.session.commit()
    print("Tabelas criadas e dados migrados com sucesso!")
