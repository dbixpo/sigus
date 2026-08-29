#!/usr/bin/env python3
"""
Script para criar o banco de dados SAMU do zero.
Executa: criação do banco, schema (tabelas), dados iniciais e usuário administrador.
"""
import os
import sys

# Adiciona o diretório raiz do projeto ao path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Credenciais (mesmo padrão do .env)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '@Qweszxc7895123')
DB_NAME = os.environ.get('DB_NAME', 'samu')


def criar_banco():
    """Cria o banco de dados se não existir."""
    import pg8000.native
    conn = pg8000.native.Connection(DB_USER, password=DB_PASSWORD, host=DB_HOST)
    rows = conn.run('SELECT 1 FROM pg_database WHERE datname = :n', n=DB_NAME)
    if not rows:
        if not DB_NAME.replace('_', '').isalnum():
            raise ValueError(f'Nome do banco inválido: {DB_NAME}')
        conn.run(f'CREATE DATABASE "{DB_NAME}"')
        print(f'Banco "{DB_NAME}" criado.')
    else:
        print(f'Banco "{DB_NAME}" já existe.')
    conn.close()


def executar_sql(conn, sql: str):
    """Executa SQL (suporta múltiplos statements separados por ;)."""
    for stmt in (s.strip() for s in sql.split(';') if s.strip()):
        conn.run(stmt)


def executar_schema(conn):
    """Aplica o schema (01_schema.sql)."""
    path = os.path.join(os.path.dirname(__file__), '01_schema.sql')
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    executar_sql(conn, sql)
    print('Schema aplicado.')


def _executar_sql_file(conn, filename, msg=''):
    """Executa um arquivo SQL opcional."""
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        for stmt in (s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')):
            try:
                conn.run(stmt)
                if msg:
                    print(msg)
            except Exception as e:
                print(f'Aviso {filename}: {e}')

def executar_matriculas(conn):
    """Cria tabela de matrículas profissionais."""
    path = os.path.join(os.path.dirname(__file__), '04_matriculas_profissionais.sql')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        executar_sql(conn, sql)
        print('Tabela matriculas_profissionais criada.')


def executar_alter_perfil(conn):
    """Altera coluna perfil para suportar múltiplos perfis."""
    path = os.path.join(os.path.dirname(__file__), '03_alter_perfil_multi.sql')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        for stmt in (s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')):
            try:
                conn.run(stmt)
                print('Coluna perfil atualizada para múltiplos perfis.')
            except Exception as e:
                if 'already' in str(e).lower() or 'does not exist' in str(e).lower():
                    pass  # já aplicado ou coluna diferente
                else:
                    print(f'Aviso: {e}')

def executar_unidades_refactor(conn):
    """Tipos de Unidade, Bases Descentralizadas, alterações em unidades_samu."""
    path = os.path.join(os.path.dirname(__file__), '06_unidades_samu_refactor.sql')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        for stmt in (s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')):
            try:
                conn.run(stmt)
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    pass
                else:
                    print(f'Aviso 06: {e}')
        print('Unidades SAMU refatoradas (tipos, bases).')


def executar_dados_iniciais(conn):
    """Aplica dados iniciais (02_dados_iniciais.sql)."""
    path = os.path.join(os.path.dirname(__file__), '02_dados_iniciais.sql')
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    executar_sql(conn, sql)
    print('Dados iniciais inseridos.')


def criar_admin(conn):
    """Cria o usuário administrador padrão."""
    from werkzeug.security import generate_password_hash

    rows = conn.run("SELECT 1 FROM usuarios WHERE usuario = :u", u='administrador.sd')
    if rows:
        print('Usuário admin já existe.')
        return

    senha_hash = generate_password_hash('@Qweszxc7895123')
    conn.run(
        """INSERT INTO usuarios (usuario, senha_hash, perfil, ativo, nome, criado_em, atualizado_em)
           VALUES (:u, :h, :p, TRUE, :n, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
        u='administrador.sd', h=senha_hash, p='administrador', n='Administrador Saúde Digital'
    )
    print('Usuário admin criado: administrador.sd / @Qweszxc7895123')


def main():
    print('=' * 50)
    print('Sistema SAMU 192 - Setup do Banco de Dados')
    print('=' * 50)

    criar_banco()

    import pg8000.native
    conn = pg8000.native.Connection(
        DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME
    )

    try:
        executar_schema(conn)
        executar_alter_perfil(conn)
        executar_matriculas(conn)
        _executar_sql_file(conn, '05_perfil_unico.sql', 'Perfis migrados para único.')
        executar_dados_iniciais(conn)
        executar_unidades_refactor(conn)
        _executar_sql_file(conn, '07_veiculos.sql', 'Tabela veiculos criada.')
        _executar_sql_file(conn, '08_unidades_saude_refactor.sql', 'Unidades de Saúde refatoradas (tipos, campos).')
        _executar_sql_file(conn, '09_protocolos_acolhimento.sql', 'Protocolos de acolhimento (palavras-chave, perguntas).')
        _executar_sql_file(conn, 'add_avisos.sql', 'Tabela avisos criada.')
        _executar_sql_file(conn, 'add_regulacao_medica.sql', 'Regulação médica (classificacoes_risco, campos ocorrência).')
        _executar_sql_file(conn, 'add_tipo_unidade_icon.sql', 'Ícone em tipos_unidade_samu.')
        _executar_sql_file(conn, 'add_despacho_ro.sql', 'Despacho RO: timestamps e cancelamento.')
        _executar_sql_file(conn, 'add_equipes.sql', 'Tabelas equipes e equipes_membros criadas.')
        _executar_sql_file(conn, 'add_equipes_perfil.sql', 'Coluna perfil em equipes_membros.')
        criar_admin(conn)
    finally:
        conn.close()

    print('=' * 50)
    print('Concluído! Acesse com: administrador.sd / @Qweszxc7895123')
    print('=' * 50)


if __name__ == '__main__':
    main()
