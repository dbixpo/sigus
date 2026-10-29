#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gera database/sigus_inicial.sql a partir do banco local.

Copia o banco, apaga pessoas (usuários, CPF, e-mail, senha, RH, frequência,
solicitações, fichas, NSP, chamados) e deixa um administrador genérico:
admin@localhost / sigus-inicial.

Só roda se a DATABASE_URL for localhost. Não altera o banco sigus.
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, unquote
from werkzeug.security import generate_password_hash

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from config import Config

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, 'database', 'sigus_inicial.sql')
BANCO_TMP = 'sigus_inicial'
EMAIL_ADMIN = 'admin@localhost'
SENHA_ADMIN = 'sigus-inicial'

# Some da base. O esquema fica; as linhas saem.
APAGAR = [
    'acao_local_comentarios',
    'acao_local_curtidas',
    'acao_planejamento_responsaveis',
    'acoes_planejamento_obs_anexos',
    'acoes_planejamento_observacoes',
    'agenda_evento_participantes',
    'agenda_eventos',
    'andamento_anexos',
    'auditoria',
    'chamado_atribuidos',
    'chamado_fotos',
    'chamado_historico',
    'chamado_solicitacao_itens',
    'chamados',
    'comunicado_ciencias',
    'equipamento_usuarios',
    'faltas_abonadas',
    'ficha_cnes_vinculo',
    'freq_horas_extras',
    'freq_importacoes',
    'freq_lancamentos',
    'matriculas_profissionais',
    'notificacoes',
    'nsp_acoes',
    'nsp_andamentos',
    'nsp_anexos',
    'nsp_encaminhamentos',
    'nsp_membros',
    'nsp_ocorrencias',
    'planejamento_alteracoes',
    'rh_servidores',
    'solicitacoes_vinculo',
    'usuario_setor',
    'usuario_unidade',
]


def params_url(url):
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


def exe(nome):
    if sys.platform != 'win32':
        return nome
    for ver in (18, 17, 16, 15):
        caminho = os.path.join(rf'C:\Program Files\PostgreSQL\{ver}\bin', nome + '.exe')
        if os.path.isfile(caminho):
            return caminho
    return nome


def psql_env(params):
    env = os.environ.copy()
    if params['password']:
        env['PGPASSWORD'] = params['password']
    env['PGCLIENTENCODING'] = 'UTF8'
    return env


def url_banco(url, nome):
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    parsed = urlparse(url)
    return parsed._replace(path='/' + nome).geturl()


def main():
    url = Config.SQLALCHEMY_DATABASE_URI
    params = params_url(url)
    if params['host'] not in ('localhost', '127.0.0.1'):
        print('  [ERRO] Este script só copia um banco em localhost.')
        sys.exit(1)
    if params['dbname'] == BANCO_TMP:
        print('  [ERRO] DATABASE_URL já aponta para o banco temporário.')
        sys.exit(1)

    print(f'  Origem: {params["host"]}/{params["dbname"]}')
    print(f'  Cópia:  {BANCO_TMP}')

    env = psql_env(params)
    psql = exe('psql')
    pg_dump = exe('pg_dump')
    base = ['-h', params['host'], '-p', str(params['port']), '-U', params['user']]

    admin = create_engine(url_banco(url, 'postgres'), isolation_level='AUTOCOMMIT')
    with admin.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :n AND pid <> pg_backend_pid()"
        ), {'n': BANCO_TMP})
        conn.execute(text(f'DROP DATABASE IF EXISTS {BANCO_TMP}'))
        conn.execute(text(f'CREATE DATABASE {BANCO_TMP}'))
    admin.dispose()

    dump = subprocess.Popen(
        [pg_dump, *base, '-d', params['dbname'], '--no-owner', '--no-acl'],
        stdout=subprocess.PIPE, env=env,
    )
    restaura = subprocess.run(
        [psql, *base, '-d', BANCO_TMP, '-v', 'ON_ERROR_STOP=1'],
        stdin=dump.stdout, env=env, capture_output=True,
    )
    dump.stdout.close()
    dump.wait()
    if restaura.returncode != 0 or dump.returncode != 0:
        erro = (restaura.stderr or b'').decode('utf-8', 'replace')[-2000:]
        print('  [ERRO] Falha ao copiar o banco.')
        print(erro)
        sys.exit(1)

    destino = create_engine(url_banco(url, BANCO_TMP))
    with destino.begin() as conn:
        segredos = _coletar_segredos(conn)
        _anular_fks_usuario(conn)
        _apagar_pessoas(conn)
        _limpar_texto(conn, segredos)
        _contato_avulso(conn)
        _criar_admin(conn)
        conn.execute(text('DELETE FROM usuarios WHERE email <> :e'), {'e': EMAIL_ADMIN})
    with destino.connect() as conn:
        n = conn.execute(text('SELECT count(*) FROM usuarios')).scalar()
        com_cpf = conn.execute(text(
            "SELECT count(*) FROM usuarios WHERE cpf IS NOT NULL AND cpf <> ''"
        )).scalar()
        rh = conn.execute(text("SELECT to_regclass('public.rh_servidores')")).scalar()
        n_rh = 0
        if rh:
            n_rh = conn.execute(text('SELECT count(*) FROM rh_servidores')).scalar()
    destino.dispose()
    if n != 1 or com_cpf or n_rh:
        print(f'  [ERRO] Limpeza incompleta (usuarios={n}, cpf={com_cpf}, rh={n_rh}).')
        sys.exit(1)

    with open(DESTINO, 'w', encoding='utf-8', newline='\n') as saida:
        saida.write(
            '-- Base inicial do SIGUS, sem cadastro de pessoas.\n'
            '-- Primeiro acesso: admin@localhost / sigus-inicial\n'
            '-- Troque essa senha depois de entrar.\n'
            '-- Gere de novo com: python scripts/gerar_dump_inicial.py\n'
            '\n'
        )
        saida.flush()
        proc = subprocess.run(
            [pg_dump, *base, '-d', BANCO_TMP, '--no-owner', '--no-acl'],
            stdout=saida, env=env,
        )
    if proc.returncode != 0:
        print('  [ERRO] pg_dump da base inicial falhou.')
        sys.exit(1)

    sobrou = _vazamento(DESTINO, segredos)
    with admin.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :n AND pid <> pg_backend_pid()"
        ), {'n': BANCO_TMP})
        conn.execute(text(f'DROP DATABASE IF EXISTS {BANCO_TMP}'))
    admin.dispose()

    if sobrou:
        os.remove(DESTINO)
        print(f'  [ERRO] O arquivo ainda tinha dado de pessoa ({sobrou} ocorrências). Nada foi gravado.')
        sys.exit(1)

    mb = os.path.getsize(DESTINO) / (1024 * 1024)
    print(f'  [OK] {DESTINO}')
    print(f'  [OK] {mb:.2f} MB')
    print(f'  [OK] Login: {EMAIL_ADMIN} / {SENHA_ADMIN}')


def _coletar_segredos(conn):
    """CPF, e-mail, senha e nome completo. A lista não é impressa."""
    valores = set()

    def add(sql):
        for (valor,) in conn.execute(text(sql)):
            if not valor:
                continue
            texto = str(valor).strip()
            if texto:
                valores.add(texto)
            digitos = ''.join(c for c in texto if c.isdigit())
            if len(digitos) == 11:
                valores.add(digitos)

    add("SELECT cpf FROM usuarios WHERE cpf IS NOT NULL")
    add("SELECT email FROM usuarios")
    add("SELECT senha_hash FROM usuarios")
    add("SELECT cns FROM usuarios WHERE cns IS NOT NULL")
    add("""
        SELECT nome FROM usuarios
        WHERE nome IS NOT NULL AND length(nome) >= 10 AND position(' ' in nome) > 0
    """)
    if conn.execute(text("SELECT to_regclass('public.rh_servidores')")).scalar():
        add("""
            SELECT nome FROM rh_servidores
            WHERE nome IS NOT NULL AND length(nome) >= 10 AND position(' ' in nome) > 0
        """)
    if conn.execute(text("SELECT to_regclass('public.solicitacoes_vinculo')")).scalar():
        add("SELECT cpf FROM solicitacoes_vinculo WHERE cpf IS NOT NULL")
        add("SELECT email FROM solicitacoes_vinculo WHERE email IS NOT NULL")
        add("""
            SELECT nome FROM solicitacoes_vinculo
            WHERE nome IS NOT NULL AND length(nome) >= 10 AND position(' ' in nome) > 0
        """)
    if conn.execute(text("SELECT to_regclass('public.nsp_ocorrencias')")).scalar():
        add("SELECT cpf FROM nsp_ocorrencias WHERE cpf IS NOT NULL")
        add("SELECT cns FROM nsp_ocorrencias WHERE cns IS NOT NULL")
        add("SELECT prontuario FROM nsp_ocorrencias WHERE prontuario IS NOT NULL")
        add("""
            SELECT nome_afetado FROM nsp_ocorrencias
            WHERE nome_afetado IS NOT NULL AND length(nome_afetado) >= 10
              AND position(' ' in nome_afetado) > 0
        """)
    return valores


def _anular_fks_usuario(conn):
    fks = conn.execute(text("""
        SELECT n.nspname, c.relname, a.attname, a.attnotnull
        FROM pg_constraint fk
        JOIN pg_class c ON c.oid = fk.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class c2 ON c2.oid = fk.confrelid
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY (fk.conkey)
        WHERE fk.contype = 'f'
          AND c2.relname = 'usuarios'
          AND n.nspname = 'public'
    """)).fetchall()
    for schema, tabela, coluna, obrigatoria in fks:
        if tabela in APAGAR or tabela == 'usuarios':
            continue
        if obrigatoria:
            raise SystemExit(f'FK obrigatória inesperada: {tabela}.{coluna}')
        conn.execute(text(
            f'UPDATE {schema}.{tabela} SET {coluna} = NULL WHERE {coluna} IS NOT NULL'
        ))


def _apagar_pessoas(conn):
    existentes = []
    for tabela in APAGAR:
        if conn.execute(text('SELECT to_regclass(:n)'), {'n': f'public.{tabela}'}).scalar():
            existentes.append(tabela)
    if existentes:
        lista = ', '.join(existentes)
        conn.execute(text(f'TRUNCATE {lista} RESTART IDENTITY'))


def _limpar_texto(conn, segredos):
    if not segredos:
        return
    conn.execute(text('CREATE TEMP TABLE _sigilos (valor text PRIMARY KEY)'))
    for valor in segredos:
        if len(valor) < 6:
            continue
        conn.execute(text(
            'INSERT INTO _sigilos (valor) VALUES (:v) ON CONFLICT DO NOTHING'
        ), {'v': valor})
    colunas = conn.execute(text("""
        SELECT table_schema, table_name, column_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema IN ('public', 'sueq')
          AND data_type IN ('text', 'character varying', 'character')
          AND (character_maximum_length IS NULL OR character_maximum_length >= 20)
          AND table_name <> 'usuarios'
          AND table_name <> 'identidade_sistema'
          AND NOT (table_name = 'unidades' AND column_name IN ('nome', 'email', 'telefone'))
          AND NOT (table_name = 'salas' AND column_name = 'nome')
          AND NOT (table_name = 'predios' AND column_name IN ('nome', 'telefone'))
          AND NOT (column_name = 'nome' AND table_name LIKE 'tipo%')
          AND NOT (table_name IN ('marcas', 'modelos', 'categorias_equipamento', 'cbos',
                                  'feriados', 'divisoes', 'setores_manutencao',
                                  'status_chamados', 'status_de_equipamento',
                                  'empresas_contratadas', 'rh_locais', 'veiculo_modelos',
                                  'nsp_catalogos', 'identidade_sistema', 'links_uteis',
                                  'parlamentares')
                   AND column_name IN ('nome', 'nome_sistema', 'dominio_email', 'titulo'))
    """)).fetchall()
    for schema, tabela, coluna, anulavel in colunas:
        if schema == 'public' and tabela in APAGAR:
            continue
        novo = 'NULL' if anulavel == 'YES' else "'[removido]'"
        conn.execute(text(f'''
            UPDATE {schema}.{tabela}
               SET {coluna} = {novo}
             WHERE {coluna} IS NOT NULL
               AND EXISTS (
                    SELECT 1 FROM _sigilos s
                    WHERE length(s.valor) >= 6
                      AND strpos(lower({schema}.{tabela}.{coluna}), lower(s.valor)) > 0
               )
        '''))


def _contato_avulso(conn):
    if conn.execute(text("SELECT to_regclass('public.contratos')")).scalar():
        conn.execute(text(
            'UPDATE contratos SET contato_nome_telefone = NULL WHERE contato_nome_telefone IS NOT NULL'
        ))
    if conn.execute(text("SELECT to_regclass('public.historico_equipamento')")).scalar():
        conn.execute(text(
            'UPDATE historico_equipamento SET observacao = NULL WHERE observacao IS NOT NULL'
        ))
    if conn.execute(text("SELECT to_regclass('sueq.chamados')")).scalar():
        conn.execute(text('''
            UPDATE sueq.chamados
               SET telefone = NULL,
                   email_retorno = NULL,
                   responsavel = NULL,
                   fiscalizado_por = NULL
             WHERE telefone IS NOT NULL
                OR email_retorno IS NOT NULL
                OR responsavel IS NOT NULL
                OR fiscalizado_por IS NOT NULL
        '''))
    if conn.execute(text("SELECT to_regclass('sueq.chamados_controle')")).scalar():
        conn.execute(text('''
            UPDATE sueq.chamados_controle
               SET fiscalizado_por = NULL
             WHERE fiscalizado_por IS NOT NULL
        '''))


def _criar_admin(conn):
    conn.execute(text('''
        INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo, criado_em, atualizado_em)
        VALUES (
            'Administrador', :email, :senha, 'administrador', true, now(), now()
        )
    '''), {
        'email': EMAIL_ADMIN,
        'senha': generate_password_hash(SENHA_ADMIN),
    })


def _vazamento(caminho, segredos):
    with open(caminho, encoding='utf-8', errors='replace') as arquivo:
        texto = arquivo.read().lower()
    alvos = [v.lower() for v in segredos if len(v) >= 6 and v.lower() != EMAIL_ADMIN]
    presentes = [v for v in alvos if v in texto]
    emails = sum(1 for v in presentes if '@' in v)
    hashes = sum(1 for v in presentes if v.startswith(('pbkdf2', 'scrypt', '$')))
    cpfs = sum(1 for v in presentes if v.isdigit() and len(v) == 11)
    print(
        f'  Conferência: emails={emails} senhas={hashes} '
        f'cpfs={cpfs} outros={len(presentes) - emails - hashes - cpfs}'
    )
    tabelas = {}
    bloco = 'inicio'
    for linha in texto.splitlines():
        if linha.startswith('copy '):
            bloco = linha.split(' ', 2)[1]
            tabelas.setdefault(bloco, 0)
        else:
            for valor in presentes:
                if valor in linha:
                    tabelas[bloco] = tabelas.get(bloco, 0) + 1
                    break
    for bloco, qtd in sorted(tabelas.items(), key=lambda item: -item[1]):
        if qtd:
            print(f'  Em {bloco}: {qtd} linhas')
    return len(presentes)


if __name__ == '__main__':
    main()
