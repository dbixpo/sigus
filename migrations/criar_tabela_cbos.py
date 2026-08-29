# -*- coding: utf-8 -*-
"""Cria tabela de CBOs e popula com os CBOs existentes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.cbo import CBO
from app.models.usuario import CBOS as CBOS_LIST
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Importa todos os modelos para garantir que o SQLAlchemy os reconheça
    from app.models.cbo import CBO
    
    # Primeiro, tenta criar usando db.create_all() (SQLAlchemy)
    try:
        db.create_all()
        print("OK: Tabela criada via SQLAlchemy create_all()")
    except Exception as e:
        print(f"AVISO ao criar via SQLAlchemy: {e}")
    
    # Depois, garante criação via SQL direto (se não existir)
    with db.engine.connect() as conn:
        # Verifica se a tabela existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'cbos'
            )
        """))
        existe = result.scalar()
        
        if not existe:
            print("Criando tabela cbos via SQL direto...")
            conn.execute(text("""
                CREATE TABLE cbos (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(10) NOT NULL UNIQUE,
                    descricao VARCHAR(200) NOT NULL,
                    ativo BOOLEAN NOT NULL DEFAULT TRUE,
                    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("OK: Tabela cbos criada com sucesso!")
        else:
            print("OK: Tabela cbos ja existe.")
    
    # Popula com os CBOs existentes
    inseridos = 0
    for codigo, descricao in CBOS_LIST:
        cbo_existente = CBO.query.filter_by(codigo=codigo).first()
        if not cbo_existente:
            cbo = CBO(codigo=codigo, descricao=descricao, ativo=True)
            db.session.add(cbo)
            inseridos += 1
    
    if inseridos > 0:
        db.session.commit()
        print(f"OK: {inseridos} CBOs inseridos na tabela.")
    else:
        print(f"OK: Todos os {len(CBOS_LIST)} CBOs ja estavam cadastrados.")
    
    total = CBO.query.count()
    print(f"OK: Total de CBOs no banco: {total}")
