# -*- coding: utf-8 -*-
"""Verifica se a tabela cbos existe e mostra informações."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Mostra qual banco está sendo usado
    from config import config
    db_url = config[app.config.get('ENV', 'default')].SQLALCHEMY_DATABASE_URI
    print(f"Banco de dados configurado: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    # Verifica se a tabela existe
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'cbos'
            )
        """))
        existe = result.scalar()
        
        if existe:
            print("OK: Tabela 'cbos' existe no banco.")
            
            # Conta quantos CBOs existem
            result = conn.execute(text("SELECT COUNT(*) FROM cbos"))
            total = result.scalar()
            print(f"Total de CBOs na tabela: {total}")
            
            # Mostra alguns exemplos
            result = conn.execute(text("SELECT codigo, descricao, ativo FROM cbos ORDER BY codigo LIMIT 5"))
            print("\nPrimeiros 5 CBOs:")
            for row in result:
                print(f"  {row[0]} - {row[1]} ({'Ativo' if row[2] else 'Inativo'})")
        else:
            print("ERRO: Tabela 'cbos' NAO existe no banco!")
            print("Execute: python migrations\\criar_tabela_cbos.py")
