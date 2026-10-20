# -*- coding: utf-8 -*-
"""
Importa dados SUEQ a partir do backup Supabase do Patrick (data.sql COPY).

Não executa roles.sql/schema.sql do Supabase no banco do SIGUS.
Só carrega tabelas usadas pelo módulo sueq, mapeando colunas comuns.

Uso (raiz do repo):
  .\\venv\\Scripts\\python.exe migrations\\import_sueq_from_supabase.py
  # ou com caminho explícito:
  ... import_sueq_from_supabase.py "C:\\Users\\dbixpo\\Desktop\\patrick\\data.sql"
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

# Ordem respeita FKs internas do schema sueq
TABLES = [
    'parlamentares',
    'unidades',
    'processos',
    'emendas',
    'emenda_itens',
    'chamados',
    'chamados_controle',
]

# Colunas do dump que NÃO existem (ou não usamos) no schema sueq do SIGUS
# — qualquer outra coluna do COPY que não esteja em sueq também é ignorada.
SKIP_SOURCE_COLS = {
    'partido', 'revisado', 'secao_id', 'status_id', 'request_id',
    'gera_mais_contratos', 'tipo_servico', 'servico_mensal_itens',
    'servico_mensal_meses', 'servico_mensal_valor_mensal',
    'servico_mensal_valor_global', 'servico_demanda_meses',
    'servico_trimestral_itens', 'servico_trimestral_meses',
    'servico_trimestral_ciclos', 'servico_trimestral_valor_trimestral',
    'servico_trimestral_valor_global', 'categoria_id',
    'medicao_id', 'nota_fiscal_id', 'termo_ateste_id',
}


def _parse_copy_blocks(path: Path):
    """Retorna {tabela: (cols_list, rows_as_tab_separated_lines)}."""
    text_data = path.read_text(encoding='utf-8')
    out = {}
    i = 0
    lines = text_data.splitlines()
    while i < len(lines):
        line = lines[i]
        if line.startswith('COPY "public".'):
            # COPY "public"."emendas" ("id", "tipo", ...) FROM stdin;
            try:
                rest = line.split('"public".', 1)[1]
                table = rest.split('"', 2)[1]
                cols_part = rest.split('(', 1)[1].rsplit(')', 1)[0]
                cols = [c.strip().strip('"') for c in cols_part.split(',')]
            except Exception:
                i += 1
                continue
            i += 1
            rows = []
            while i < len(lines) and lines[i] != '\\.':
                rows.append(lines[i])
                i += 1
            out[table] = (cols, rows)
        i += 1
    return out


def _target_columns(schema_cols, source_cols):
    """Interseção na ordem do dump (estável para COPY)."""
    schema_set = set(schema_cols)
    return [c for c in source_cols if c in schema_set and c not in SKIP_SOURCE_COLS]


def main():
    default = Path(r'C:\Users\dbixpo\Desktop\patrick\data.sql')
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not data_path.is_file():
        print(f'ERRO: arquivo não encontrado: {data_path}')
        sys.exit(1)

    print(f'Lendo {data_path} ...')
    blocks = _parse_copy_blocks(data_path)
    missing = [t for t in TABLES if t not in blocks]
    if missing:
        print('ERRO: tabelas ausentes no data.sql:', ', '.join(missing))
        sys.exit(1)

    app = create_app()
    with app.app_context():
        # Colunas atuais em sueq.*
        with db.engine.connect() as conn:
            schema_map = {}
            for t in TABLES:
                cols = [
                    r[0] for r in conn.execute(text("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema='sueq' AND table_name=:t
                        ORDER BY ordinal_position
                    """), {'t': t})
                ]
                if not cols:
                    print(f'ERRO: sueq.{t} não existe — rode migrations/add_sueq_schema.py primeiro.')
                    sys.exit(1)
                schema_map[t] = cols

        raw = db.engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.execute('SET client_encoding TO UTF8')
            # Limpa dados atuais (idempotente para reimport)
            cur.execute(
                'TRUNCATE TABLE '
                + ', '.join(f'sueq.{t}' for t in reversed(TABLES))
                + ' RESTART IDENTITY CASCADE'
            )

            for table in TABLES:
                src_cols, rows = blocks[table]
                tgt_cols = _target_columns(schema_map[table], src_cols)
                if not tgt_cols:
                    print(f'AVISO: {table} sem colunas mapeáveis — pulando')
                    continue
                idx = [src_cols.index(c) for c in tgt_cols]
                # Monta TSV só com colunas-alvo
                filtered = []
                for row in rows:
                    if not row.strip():
                        continue
                    parts = row.split('\t')
                    if len(parts) < len(src_cols):
                        # linha incompleta — preenche
                        parts = parts + ['\\N'] * (len(src_cols) - len(parts))
                    filtered.append('\t'.join(parts[j] for j in idx))
                payload = '\n'.join(filtered) + ('\n' if filtered else '')
                col_list = ', '.join(f'"{c}"' for c in tgt_cols)
                sql = f'COPY sueq.{table} ({col_list}) FROM STDIN WITH (FORMAT text, NULL \'\\N\')'
                cur.copy_expert(sql, __import__('io').StringIO(payload))
                print(f'OK sueq.{table}: {len(filtered)} linhas ({len(tgt_cols)} cols)')

            # Ajusta sequences dos bigint
            for table in ('parlamentares', 'unidades', 'processos'):
                cur.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence('sueq.{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM sueq.{table}), 1),
                        true
                    )
                """)

            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()

        with db.engine.connect() as conn:
            for t in TABLES:
                n = conn.execute(text(f'SELECT COUNT(*) FROM sueq.{t}')).scalar()
                print(f'  count {t} = {n}')

    print('OK: import SUEQ concluído (sem storage/chamados-fotos).')


if __name__ == '__main__':
    main()
