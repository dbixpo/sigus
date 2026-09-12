#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Importa o backup de produção do Patrick (Supabase contratos-dag)
para o PostgreSQL local no schema `sueq`, sem tocar no SIGUS (public).

Fonte (dump local, não versionar): pasta combinada com a equipe (schema.sql, data.sql, storage).
Não apontar caminho de máquina pessoal neste arquivo.
            chamados-fotos/           — ignorado (provisório, 3 meses)
            notas-fiscais/
            termos-entrega/
            inventario-movimentacoes/
            licitacao-ocorrencias/    — bucket vazio, só a pasta

Uso (na raiz do SIGUS):
    python scripts/importar_schema_sueq.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
from zipfile import ZipFile

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

SRC_DIR = Path(r'C:\Users\hardr\Desktop\patrick')
SRC_SCHEMA = SRC_DIR / 'schema.sql'
SRC_DATA = SRC_DIR / 'data.sql'
SRC_STORAGE = SRC_DIR / 'supabase-storage.zip'

OUT_SCHEMA = ROOT / 'database' / 'sueq_schema.sql'
OUT_DATA = ROOT / 'database' / 'sueq_data.sql'
STORAGE_DEST = ROOT / 'app' / 'static' / 'uploads' / 'sueq'

SKIP_BUCKETS = {'chamados-fotos'}
EMPTY_BUCKETS = ('licitacao-ocorrencias',)


def parse_database_url(url):
    if not url:
        return None
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': unquote(parsed.username) if parsed.username else 'postgres',
        'password': unquote(parsed.password) if parsed.password else '',
        'dbname': (parsed.path or '/sigus').lstrip('/') or 'sigus',
    }


def encontrar_psql():
    import shutil as sh
    if sh.which('psql'):
        return 'psql'
    for ver in range(18, 11, -1):
        candidate = rf'C:\Program Files\PostgreSQL\{ver}\bin\psql.exe'
        if os.path.exists(candidate):
            return candidate
    return 'psql'


def rewrite_public(sql: str) -> str:
    return sql.replace('"public".', '"sueq".').replace('public.', 'sueq.')


def sanitize(sql: str) -> str:
    sql = sql.replace('"auth"."uid"()', 'NULL')
    sql = sql.replace('auth.uid()', 'NULL')
    return sql


def is_backup_name(name: str) -> bool:
    return 'backup' in name.lower()


def refs_supabase(blob: str) -> bool:
    u = blob.upper()
    return (
        'REFERENCES "AUTH"' in u
        or 'REFERENCES AUTH.' in u
        or 'REFERENCES "STORAGE"' in u
        or 'REFERENCES STORAGE.' in u
        or 'REFERENCES "VAULT"' in u
        or 'REFERENCES "SUPABASE' in u
    )


def extract_schema(text: str) -> str:
    parts = [
        '-- Schema SUEQ gerado do backup de produção (10/09/2026)',
        '-- Fonte: Desktop/patrick/schema.sql  |  projeto qpvgpfwuurqcqprnpxua',
        'CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;',
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;',
        'CREATE SCHEMA IF NOT EXISTS sueq;',
        'SET search_path TO sueq, public;',
        '',
    ]

    seq_re = re.compile(
        r'CREATE SEQUENCE IF NOT EXISTS "public"\."([^"]+)"(.*?);',
        re.S,
    )
    for name, body in seq_re.findall(text):
        if is_backup_name(name):
            continue
        parts.append(rewrite_public(
            f'CREATE SEQUENCE IF NOT EXISTS "public"."{name}"{body};'
        ))
        parts.append('')

    table_re = re.compile(
        r'CREATE TABLE IF NOT EXISTS "public"\."([^"]+)" \((.*?)\n\);',
        re.S,
    )
    for name, body in table_re.findall(text):
        if is_backup_name(name):
            continue
        parts.append(sanitize(rewrite_public(
            f'CREATE TABLE IF NOT EXISTS "public"."{name}" ({body}\n);'
        )))
        parts.append('')

    ident_re = re.compile(
        r'ALTER TABLE "public"\."([^"]+)" ALTER COLUMN "([^"]+)" '
        r'ADD GENERATED (ALWAYS|BY DEFAULT) AS IDENTITY \(\s*SEQUENCE NAME "public"\."([^"]+)"(.*?)\);',
        re.S,
    )
    for table, col, kind, seq, rest in ident_re.findall(text):
        if is_backup_name(table) or is_backup_name(seq):
            continue
        parts.append(rewrite_public(
            f'ALTER TABLE "public"."{table}" ALTER COLUMN "{col}" '
            f'ADD GENERATED {kind} AS IDENTITY (\n    SEQUENCE NAME "public"."{seq}"{rest});'
        ))
        parts.append('')

    pk_fk_re = re.compile(
        r'ALTER TABLE ONLY "public"\."([^"]+)"\s+ADD CONSTRAINT "([^"]+)" (.*?);',
        re.S,
    )
    for table, constraint, body in pk_fk_re.findall(text):
        if is_backup_name(table) or is_backup_name(constraint):
            continue
        if refs_supabase(f'{constraint} {body}'):
            continue
        parts.append(rewrite_public(
            f'ALTER TABLE ONLY "public"."{table}"\n    ADD CONSTRAINT "{constraint}" {body};'
        ))
        parts.append('')

    idx_re = re.compile(
        r'CREATE (UNIQUE )?INDEX (?:IF NOT EXISTS )?"([^"]+)" ON "public"\."([^"]+)" USING ([^;]+);',
        re.S,
    )
    for unique, idx, table, using in idx_re.findall(text):
        if is_backup_name(table) or is_backup_name(idx):
            continue
        if refs_supabase(using):
            continue
        uniq = 'UNIQUE ' if unique else ''
        parts.append(rewrite_public(
            f'CREATE {uniq}INDEX IF NOT EXISTS "{idx}" ON "public"."{table}" USING {using};'
        ))
        parts.append('')

    parts.append('ALTER TABLE sueq.emendas ADD COLUMN IF NOT EXISTS link_sei text;')
    parts.append('')
    return '\n'.join(parts)


def extract_data(src: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    counts = {}
    copy_re = re.compile(r'^COPY "([^"]+)"\."([^"]+)"')
    setval_re = re.compile(r"^SELECT pg_catalog\.setval\('\"public\"")

    with src.open(encoding='utf-8', errors='replace') as inf, dest.open(
        'w', encoding='utf-8', newline='\n'
    ) as out:
        out.write("-- Dados de produção SUEQ (public → sueq). Não versionar.\n")
        out.write("SET session_replication_role = replica;\n")
        out.write("SET client_encoding = 'UTF8';\n")
        out.write("SET search_path TO sueq, public;\n\n")

        in_copy = False
        keep = False
        current = None
        nrows = 0
        for line in inf:
            if line.startswith('\\restrict') or line.startswith('\\unrestrict'):
                continue
            if line.startswith('COPY "'):
                m = copy_re.match(line)
                schema, table = m.group(1), m.group(2)
                keep = schema == 'public' and not is_backup_name(table)
                in_copy = True
                current = table
                nrows = 0
                if keep:
                    out.write(rewrite_public(line))
                continue
            if in_copy:
                if keep:
                    out.write(line)
                    if not line.startswith('\\.'):
                        nrows += 1
                if line.startswith('\\.'):
                    if keep:
                        counts[current] = nrows
                    in_copy = False
                    keep = False
                    current = None
                continue
            if setval_re.match(line):
                out.write(rewrite_public(line))

        out.write("\nSET session_replication_role = DEFAULT;\n")
    return counts


def extract_storage() -> dict:
    STORAGE_DEST.mkdir(parents=True, exist_ok=True)
    copied = {}
    skipped = 0
    if not SRC_STORAGE.exists():
        print(f'  [AVISO] Zip do Storage não encontrado: {SRC_STORAGE}')
        return copied
    with ZipFile(SRC_STORAGE) as z:
        for info in z.infolist():
            name = info.filename.replace('\\', '/')
            if name.endswith('/'):
                continue
            parts = name.split('/')
            if parts[0] != 'supabase-storage' or len(parts) < 2:
                continue
            bucket = parts[1]
            if bucket in SKIP_BUCKETS:
                skipped += 1
                continue
            rel = Path(*parts[1:])
            dest = STORAGE_DEST / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(dest, 'wb') as out:
                shutil.copyfileobj(src, out)
            copied[bucket] = copied.get(bucket, 0) + 1
    for bucket in EMPTY_BUCKETS:
        (STORAGE_DEST / bucket).mkdir(parents=True, exist_ok=True)
        copied.setdefault(bucket, 0)
    print(f'  Storage: copiados {sum(copied.values())} arquivos, ignorados {skipped} (chamados-fotos)')
    for k, v in sorted(copied.items()):
        print(f'    {k}: {v}')
    return copied


def main():
    if not SRC_SCHEMA.exists() or not SRC_DATA.exists():
        print(f'[ERRO] Backup do Patrick não encontrado em {SRC_DIR}')
        sys.exit(1)

    print('  Lendo schema de produção...')
    text = SRC_SCHEMA.read_text(encoding='utf-8', errors='replace')
    sql = extract_schema(text)
    OUT_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    OUT_SCHEMA.write_text(sql, encoding='utf-8')
    print(f'  SQL gerado: {OUT_SCHEMA} ({len(sql)} chars)')

    print('  Extraindo COPY de public -> sueq...')
    counts = extract_data(SRC_DATA, OUT_DATA)
    print(f'  Dados: {OUT_DATA} ({sum(counts.values())} linhas em {len(counts)} tabelas)')

    params = parse_database_url(os.environ.get('DATABASE_URL'))
    if not params:
        print('[ERRO] DATABASE_URL inválida')
        sys.exit(1)

    psql = encontrar_psql()
    env = os.environ.copy()
    if params['password']:
        env['PGPASSWORD'] = params['password']

    base = [
        psql, '-h', params['host'], '-p', str(params['port']),
        '-U', params['user'], '-d', params['dbname'], '-v', 'ON_ERROR_STOP=1',
    ]

    print('  Recriando schema sueq...')
    subprocess.run(
        base + ['-c', 'DROP SCHEMA IF EXISTS sueq CASCADE; CREATE SCHEMA sueq;'],
        env=env, check=True,
    )
    print('  Aplicando tabelas...')
    subprocess.run(base + ['-f', str(OUT_SCHEMA)], env=env, check=True)
    print('  Carregando dados de produção...')
    subprocess.run(base + ['-f', str(OUT_DATA)], env=env, check=True)

    print('  Extraindo Storage (sem chamados-fotos)...')
    extract_storage()

    print('  Contagem rápida:')
    for tabela in ('emendas', 'emenda_itens', 'processos', 'unidades', 'parlamentares', 'contratos'):
        n = counts.get(tabela, 0)
        print(f'    {tabela}: {n}')
    print('  [OK] Schema SUEQ de produção pronto.')


if __name__ == '__main__':
    main()
