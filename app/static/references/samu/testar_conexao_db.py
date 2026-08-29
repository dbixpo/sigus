#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL.
Execute: python testar_conexao_db.py
"""
import os
import sys

# Carrega .env da raiz do projeto
from pathlib import Path
root = Path(__file__).resolve().parent
os.chdir(root)

from dotenv import load_dotenv
load_dotenv()

# Mostra o que está configurado (senha mascarada)
db_user = os.environ.get('DB_USER', 'postgres')
db_pass = os.environ.get('DB_PASSWORD', '@Qweszxc7895123')
db_host = os.environ.get('DB_HOST', 'localhost')
db_name = os.environ.get('DB_NAME', 'samu')

print('=== Configuração atual ===')
print(f'DB_USER: {db_user}')
print(f'DB_PASSWORD: {"*" * len(db_pass)} ({len(db_pass)} caracteres)')
print(f'DB_HOST: {db_host}')
print(f'DB_NAME: {db_name}')
print()

# Teste direto com pg8000 (mesmo driver do Flask)
try:
    import pg8000.native
    print('Tentando conectar...')
    conn = pg8000.native.Connection(
        db_user,
        password=db_pass,
        host=db_host,
        database=db_name
    )
    conn.run('SELECT 1')
    print('OK! Conexão funcionou.')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'ERRO: {e}')
    print()
    print('Possíveis soluções:')
    print('1. Verifique se a senha do PostgreSQL está correta.')
    print('2. Teste no terminal: psql -U postgres -h localhost -d samu')
    print('3. Para alterar a senha no PostgreSQL:')
    print('   - Abra psql: psql -U postgres')
    print('   - Execute: ALTER USER postgres PASSWORD \'@Qweszxc7895123\';')
    print('4. Ou defina sua senha real no .env: DB_PASSWORD="sua_senha"')
    sys.exit(1)
