#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIGUS — Restaura o banco PostgreSQL.

Ordem: database/sigus_backup.zip, o sigus_backup_*.sql mais novo,
ou database/sigus_inicial.sql (base pública, sem pessoas).

Uso:
    python scripts/restaura_banco.py

Requer: psql no PATH (ou instalado no diretório padrão do PostgreSQL).
"""
import os
import sys
import subprocess
import zipfile
import shutil
from urllib.parse import urlparse, unquote

PROJETO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(PROJETO_DIR, 'database')

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


def encontrar_psql():
    if shutil.which('psql'):
        return 'psql'
    if sys.platform == 'win32':
        for ver in [18, 17, 16, 15, 14, 13, 12]:
            candidate = rf'C:\Program Files\PostgreSQL\{ver}\bin\psql.exe'
            if os.path.exists(candidate):
                return candidate
    return 'psql'


def main():
    print(f'\n{SEP}')
    print('  SIGUS — Restauração do Banco de Dados')
    print(SEP)

    url = Config.SQLALCHEMY_DATABASE_URI
    params = parse_database_url(url)
    if not params:
        print('  [ERRO] DATABASE_URL inválida em .env')
        sys.exit(1)

    # Localizar arquivo de backup
    zip_path = os.path.join(DATABASE_DIR, 'sigus_backup.zip')
    sql_temp = None

    if os.path.exists(zip_path):
        print(f'  Extraindo backup de: {zip_path}')
        with zipfile.ZipFile(zip_path, 'r') as zf:
            sql_files = [f for f in zf.namelist() if f.endswith('.sql')]
            if not sql_files:
                print('  [ERRO] Nenhum arquivo .sql encontrado dentro de sigus_backup.zip')
                sys.exit(1)
            target = sql_files[0]
            zf.extract(target, DATABASE_DIR)
            sql_temp = os.path.join(DATABASE_DIR, target)
    else:
        datados = [
            os.path.join(DATABASE_DIR, f)
            for f in os.listdir(DATABASE_DIR)
            if f.startswith('sigus_backup_') and f.endswith('.sql')
        ]
        if datados:
            datados.sort(key=os.path.getmtime, reverse=True)
            sql_temp = datados[0]
        else:
            inicial = os.path.join(DATABASE_DIR, 'sigus_inicial.sql')
            if not os.path.exists(inicial):
                print('  [ERRO] Nenhum backup encontrado em database/')
                print('  Esperado: sigus_backup.zip, sigus_backup_*.sql ou sigus_inicial.sql')
                sys.exit(1)
            sql_temp = inicial

    print(f'  Arquivo SQL: {sql_temp}')
    print(f'  Host: {params["host"]}:{params["port"]}')
    print(f'  Banco: {params["dbname"]}')
    print(f'  Usuário: {params["user"]}')
    print()

    psql_exe = encontrar_psql()
    env = os.environ.copy()
    if params['password']:
        env['PGPASSWORD'] = params['password']

    cmd = [
        psql_exe,
        '-h', params['host'],
        '-p', str(params['port']),
        '-U', params['user'],
        '-d', params['dbname'],
        '-f', sql_temp,
    ]

    try:
        print('  Executando restauração...')
        subprocess.run(cmd, env=env, check=True)
        print('\n  [OK] Banco restaurado com sucesso!')
    except subprocess.CalledProcessError as e:
        print(f'\n  [ERRO] Falha ao restaurar banco: {e}')
        sys.exit(1)
    except FileNotFoundError:
        print(f'\n  [ERRO] psql não encontrado. Verifique se o PostgreSQL está instalado.')
        sys.exit(1)


if __name__ == '__main__':
    main()
