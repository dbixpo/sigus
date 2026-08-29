#!/usr/bin/env python3
"""Adiciona coluna apelido em unidades_saude. Usa DATABASE_URL do Flask."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import config
from sqlalchemy import create_engine, text

url = config['default'].SQLALCHEMY_DATABASE_URI
engine = create_engine(url)
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS apelido VARCHAR(100)"))
    conn.commit()
    print("Coluna apelido adicionada em unidades_saude.")
