#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIGUS — Clona/exporta o banco PostgreSQL para a pasta database/.
O arquivo gerado pode ser restaurado no servidor com: psql -U usuario -d sigus -f arquivo.sql

Uso:
    python scripts/clone_banco.py

Requer: pg_dump no PATH (vem com PostgreSQL instalado).
"""
import os
import sys
import subprocess
from datetime import datetime
from urllib.parse import urlparse, unquote

# Raiz do projeto
PROJETO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(PROJETO_DIR, 'database')

# Carregar .env
sys.path.insert(0, PROJETO_DIR)
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJETO_DIR, '.env'))

from config import Config

SEP = '=' * 50


def parse_database_url(url):
    """Extrai host, port, user, password, dbname de uma URL PostgreSQL."""
    if not url:
        return None
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    try:
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'user': unquote(parsed.username) if parsed.username else 'postgres',
            'password': unquote(parsed.password) if parsed.password else '',
            'dbname': (parsed.path or '/sigus').lstrip('/') or 'sigus',
        }
    except Exception:
        return None


def main():
    print(f'\n{SEP}')
    print('  SIGUS — Clone do Banco de Dados')
    print(SEP)

    url = Config.SQLALCHEMY_DATABASE_URI
    params = parse_database_url(url)
    if not params:
        print('  [ERRO] DATABASE_URL inválida em .env')
        sys.exit(1)

    os.makedirs(DATABASE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    arquivo = os.path.join(DATABASE_DIR, f'sigus_backup_{timestamp}.sql')

    print(f'  Host: {params["host"]}')
    print(f'  Banco: {params["dbname"]}')
    print(f'  Saída: {arquivo}')
    print()

    # pg_dump -h HOST -p PORT -U USER -d DBNAME -F p --no-owner --no-acl -f arquivo
    # PGPASSWORD é passado via env para não aparecer no ps
    env = os.environ.copy()
    if params['password']:
        env['PGPASSWORD'] = params['password']

    cmd = [
        'pg_dump',
        '-h', params['host'],
        '-p', str(params['port']),
        '-U', params['user'],
        '-d', params['dbname'],
        '-F', 'p',
        '--no-owner',
        '--no-acl',
        '-f', arquivo,
    ]

    # Encontrar pg_dump (pode não estar no PATH no Windows)
    pg_dump_exe = 'pg_dump'
    if sys.platform == 'win32':
        for base in [
            os.environ.get('PG_HOME', ''),
            r'C:\Program Files\PostgreSQL\18\bin',
            r'C:\Program Files\PostgreSQL\17\bin',
            r'C:\Program Files\PostgreSQL\16\bin',
            r'C:\Program Files\PostgreSQL\15\bin',
        ]:
            if base:
                candidate = os.path.join(base, 'pg_dump.exe')
                if os.path.isfile(candidate):
                    pg_dump_exe = candidate
                    break

    cmd[0] = pg_dump_exe

    try:
        subprocess.run(cmd, env=env, check=True)
        size_mb = os.path.getsize(arquivo) / (1024 * 1024)
        print(f'  [OK] Backup salvo: {arquivo}')
        print(f'  [OK] Tamanho: {size_mb:.2f} MB')
        print()
        print('  Para restaurar no servidor:')
        print(f'    psql -h HOST -U usuario -d sigus -f database/sigus_backup_{timestamp}.sql')
        print()
    except FileNotFoundError:
        print('  [ERRO] pg_dump não encontrado. Instale o PostgreSQL ou adicione ao PATH.')
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f'  [ERRO] pg_dump falhou: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
