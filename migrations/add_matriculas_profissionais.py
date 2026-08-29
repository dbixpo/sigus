"""
Migração: cria tabela matriculas_profissionais e adiciona coluna
matricula_id em usuario_unidade.

Migra também os dados existentes: se um usuário já tiver usuario.matricula
preenchido, cria um registro MatriculaProfissional para ele.

Execute com:
    python migrations/add_matriculas_profissionais.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from config import Config

DSN = Config.SQLALCHEMY_DATABASE_URI.replace('+psycopg2', '')

def run():
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur  = conn.cursor()

    # 1. Criar tabela de matrículas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matriculas_profissionais (
            id            SERIAL PRIMARY KEY,
            usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            numero        VARCHAR(50) NOT NULL,
            vinculo       VARCHAR(1),
            tipo_vinculo  VARCHAR(1),
            cbo           VARCHAR(10),
            reg_conselho  VARCHAR(30),
            orgao_emissor VARCHAR(50),
            ativo         BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    print("✓ Tabela matriculas_profissionais criada (ou já existia).")

    # 2. Migrar dados existentes (usuario.matricula → nova tabela)
    cur.execute("""
        SELECT id, matricula, vinculo, tipo_vinculo, cbo, reg_conselho, orgao_emissor
        FROM usuarios
        WHERE matricula IS NOT NULL AND matricula <> ''
          AND NOT EXISTS (
              SELECT 1 FROM matriculas_profissionais mp WHERE mp.usuario_id = usuarios.id
          );
    """)
    rows = cur.fetchall()
    for uid, mat, vinc, tvinc, cbo, reg, orgao in rows:
        cur.execute("""
            INSERT INTO matriculas_profissionais
                (usuario_id, numero, vinculo, tipo_vinculo, cbo, reg_conselho, orgao_emissor)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (uid, mat, vinc, tvinc, cbo, reg, orgao))
    print(f"✓ {len(rows)} matrículas existentes migradas.")

    # 3. Adicionar coluna matricula_id em usuario_unidade
    cur.execute("""
        ALTER TABLE usuario_unidade
        ADD COLUMN IF NOT EXISTS matricula_id INTEGER
            REFERENCES matriculas_profissionais(id) ON DELETE SET NULL;
    """)
    print("✓ Coluna matricula_id adicionada em usuario_unidade.")

    conn.commit()
    cur.close()
    conn.close()
    print("✓ Migração concluída com sucesso.")

if __name__ == '__main__':
    run()
