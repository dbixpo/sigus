#!/usr/bin/env python3
"""
Corrige tabela unidades_samu: adiciona colunas da refatoração Central/Viatura.
Usa a mesma DATABASE_URL do Flask (config.py).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import config
from sqlalchemy import create_engine, text

# Usa a mesma URL que o Flask
url = config['default'].SQLALCHEMY_DATABASE_URI
print(f"Conectando em: {url.split('@')[-1] if '@' in url else url}")

engine = create_engine(url)

# Script 06: colunas da refatoração
alteracoes = [
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS tipo_registro VARCHAR(20) DEFAULT 'central'",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS apelido VARCHAR(100)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cnes VARCHAR(7)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS logradouro VARCHAR(300)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS numero VARCHAR(20)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS complemento VARCHAR(100)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS bairro VARCHAR(100)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cidade VARCHAR(100)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cep VARCHAR(9)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS email VARCHAR(200)",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS link_google_maps VARCHAR(500)",
]

# base_id e tipo_unidade_id precisam de FK - verificar se tabelas existem
alteracoes_fk = [
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS base_id INTEGER REFERENCES bases_descentralizadas(id) ON DELETE SET NULL",
    "ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS tipo_unidade_id INTEGER REFERENCES tipos_unidade_samu(id) ON DELETE SET NULL",
]

with engine.connect() as conn:
    for sql in alteracoes:
        try:
            conn.execute(text(sql))
            conn.commit()
            print(f"OK: {sql[:60]}...")
        except Exception as e:
            print(f"Erro: {e}")

    for sql in alteracoes_fk:
        try:
            conn.execute(text(sql))
            conn.commit()
            print(f"OK: {sql[:60]}...")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"Já existe: {sql[:50]}...")
            else:
                print(f"Erro FK: {e}")

    # Atualizar tipo_registro e migrar dados antigos
    try:
        conn.execute(text("UPDATE unidades_samu SET tipo_registro = 'central' WHERE tipo_registro IS NULL"))
        conn.execute(text("UPDATE unidades_samu SET logradouro = endereco WHERE logradouro IS NULL AND endereco IS NOT NULL"))
        conn.execute(text("UPDATE unidades_samu SET cidade = municipio WHERE cidade IS NULL AND municipio IS NOT NULL"))
        conn.commit()
        print("Dados migrados.")
    except Exception as e:
        print(f"Aviso migração dados: {e}")

print("Concluído. Teste: http://localhost:5192/configuracoes/unidades-samu")
