# -*- coding: utf-8 -*-
"""Veículos das unidades e reserva de salas/veículos na agenda (idempotente).

- veiculos (cadastro próprio, fora dos equipamentos: prefixo, check "alugado", placa…)
  e veiculo_modelos (catálogo de modelos populares para sugerir no cadastro)
- agenda_eventos: sala_id, veiculo_id (→ veiculos), condutor_id, km_saida, km_chegada, devolvido_em
- tipos_sala.reservavel, salas.uso_compartilhado; "Sala de Reunião" (AMB-41) reservável e tipo "Auditório"
- Permissões da seção "Veículos" copiadas das de "Equipamentos"
- Remove o que a primeira versão criou nos equipamentos (tipo "Veículo", sala/tipo "Garagem",
  marcas de carro, coluna tipos_equipamento.eh_veiculo), desde que não haja equipamento usando
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

COMANDOS = [
    "ALTER TABLE tipos_sala ADD COLUMN IF NOT EXISTS reservavel BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE salas ADD COLUMN IF NOT EXISTS uso_compartilhado BOOLEAN NOT NULL DEFAULT FALSE",
    """CREATE TABLE IF NOT EXISTS veiculo_modelos (
        id SERIAL PRIMARY KEY,
        marca VARCHAR(60) NOT NULL,
        nome VARCHAR(80) NOT NULL,
        categoria VARCHAR(40),
        UNIQUE (marca, nome)
    )""",
    """CREATE TABLE IF NOT EXISTS veiculos (
        id SERIAL PRIMARY KEY,
        unidade_id INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
        prefixo VARCHAR(20) NOT NULL,
        alugado BOOLEAN NOT NULL DEFAULT FALSE,
        locadora VARCHAR(150),
        placa VARCHAR(10) NOT NULL,
        marca VARCHAR(60),
        modelo VARCHAR(80),
        categoria VARCHAR(40),
        ano VARCHAR(9),
        cor VARCHAR(30),
        combustivel VARCHAR(20),
        lotacao INTEGER,
        renavam VARCHAR(20),
        chassi VARCHAR(30),
        km_cadastro INTEGER,
        licenciamento_vencimento DATE,
        observacoes TEXT,
        ativo BOOLEAN NOT NULL DEFAULT TRUE,
        criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
        atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_veiculos_unidade ON veiculos (unidade_id) WHERE ativo",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS sala_id INTEGER REFERENCES salas(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS veiculo_id INTEGER",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS condutor_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS km_saida INTEGER",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS km_chegada INTEGER",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS devolvido_em TIMESTAMP",
    "CREATE INDEX IF NOT EXISTS ix_agenda_eventos_sala ON agenda_eventos (sala_id, inicio) WHERE sala_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_agenda_eventos_veiculo ON agenda_eventos (veiculo_id, inicio) WHERE veiculo_id IS NOT NULL",
]

# (marca, [(modelo, categoria), ...]) — populares da frota brasileira
P, U, C, V, M, T = 'Carro de passeio', 'Utilitário', 'Caminhonete', 'Van', 'Motocicleta', 'Caminhão'
MODELOS = [
    ('Fiat', [('Mobi', P), ('Uno', P), ('Palio', P), ('Argo', P), ('Cronos', P), ('Siena', P), ('Grand Siena', P),
              ('Pulse', P), ('Fastback', P), ('Strada', C), ('Toro', C), ('Titano', C), ('Fiorino', U),
              ('Doblò', U), ('Ducato', V)]),
    ('Volkswagen', [('Gol', P), ('Voyage', P), ('Fox', P), ('Up!', P), ('Polo', P), ('Virtus', P), ('T-Cross', P),
                    ('Nivus', P), ('Tera', P), ('Saveiro', C), ('Amarok', C), ('Kombi', V), ('Delivery', T)]),
    ('Chevrolet', [('Onix', P), ('Onix Plus', P), ('Prisma', P), ('Celta', P), ('Classic', P), ('Cobalt', P),
                   ('Spin', P), ('Tracker', P), ('Montana', C), ('S10', C)]),
    ('Renault', [('Kwid', P), ('Sandero', P), ('Logan', P), ('Duster', P), ('Kardian', P), ('Oroch', C),
                 ('Kangoo', U), ('Master', V)]),
    ('Ford', [('Ka', P), ('Ka Sedan', P), ('Fiesta', P), ('EcoSport', P), ('Ranger', C), ('Maverick', C),
              ('Transit', V), ('Cargo', T)]),
    ('Toyota', [('Etios', P), ('Yaris', P), ('Corolla', P), ('Corolla Cross', P), ('SW4', P), ('Hilux', C)]),
    ('Hyundai', [('HB20', P), ('HB20S', P), ('Creta', P), ('HR', U)]),
    ('Peugeot', [('208', P), ('2008', P), ('Partner', U), ('Expert', V), ('Boxer', V)]),
    ('Citroën', [('C3', P), ('C4 Cactus', P), ('Berlingo', U), ('Jumpy', V), ('Jumper', V)]),
    ('Nissan', [('March', P), ('Versa', P), ('Kicks', P), ('Frontier', C)]),
    ('Honda', [('Fit', P), ('City', P), ('HR-V', P), ('WR-V', P), ('CG 160', M), ('Biz 125', M), ('Pop 110i', M),
               ('Bros 160', M), ('XRE 300', M)]),
    ('Yamaha', [('Factor 150', M), ('Fazer 250', M), ('Crosser 150', M)]),
    ('Jeep', [('Renegade', P), ('Compass', P)]),
    ('Mitsubishi', [('L200 Triton', C)]),
    ('Mercedes-Benz', [('Sprinter', V), ('Accelo', T)]),
    ('Iveco', [('Daily', V)]),
]

# Marcas que a primeira versão criou no catálogo de equipamentos
MARCAS_ANTIGAS = ['Fiat', 'Volkswagen', 'Chevrolet', 'Renault', 'Ford', 'Toyota', 'Hyundai', 'Peugeot',
                  'Citroën', 'Nissan', 'Honda', 'Jeep', 'Mercedes-Benz', 'Iveco', 'Mitsubishi']


def _um(conn, sql, **params):
    row = conn.execute(text(sql), params).first()
    return row[0] if row else None


def _ligar_agenda_a_veiculos(conn):
    """agenda_eventos.veiculo_id passa a apontar para veiculos (antes: equipamentos)."""
    fks = conn.execute(text("""
        SELECT c.conname, c.confrelid::regclass::text
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
        WHERE c.conrelid = 'agenda_eventos'::regclass AND c.contype = 'f' AND a.attname = 'veiculo_id'
    """)).all()
    certo = False
    for nome, alvo in fks:
        if alvo == 'veiculos':
            certo = True
            continue
        conn.execute(text("UPDATE agenda_eventos SET veiculo_id = NULL WHERE veiculo_id IS NOT NULL"))
        conn.execute(text(f'ALTER TABLE agenda_eventos DROP CONSTRAINT "{nome}"'))
        print(f'Reservas da agenda desligadas de {alvo}.')
    if not certo:
        conn.execute(text("UPDATE agenda_eventos SET veiculo_id = NULL "
                          "WHERE veiculo_id IS NOT NULL AND veiculo_id NOT IN (SELECT id FROM veiculos)"))
        conn.execute(text("""
            ALTER TABLE agenda_eventos ADD CONSTRAINT agenda_eventos_veiculo_id_fkey
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id) ON DELETE SET NULL
        """))
        print('Reservas da agenda ligadas à tabela veiculos.')


def _remover_veiculo_dos_equipamentos(conn):
    tem_coluna = _um(conn, """SELECT 1 FROM information_schema.columns
                              WHERE table_name = 'tipos_equipamento' AND column_name = 'eh_veiculo'""")
    if not tem_coluna:
        return
    tipo_id = _um(conn, "SELECT id FROM tipos_equipamento WHERE eh_veiculo ORDER BY id LIMIT 1")
    if tipo_id:
        em_uso = _um(conn, "SELECT COUNT(*) FROM equipamentos WHERE tipo_equipamento_id = :t", t=tipo_id)
        if em_uso:
            print(f'ATENÇÃO: {em_uso} equipamento(s) ainda usam o tipo "Veículo". Cadastre-os em Veículos, '
                  'apague-os dos equipamentos e rode de novo.')
            return
        conn.execute(text("DELETE FROM marca_tipo_equipamento WHERE tipo_equipamento_id = :t"), {'t': tipo_id})
        conn.execute(text("DELETE FROM modelos WHERE tipo_equipamento_id = :t"), {'t': tipo_id})
        conn.execute(text("DELETE FROM tipos_equipamento WHERE id = :t"), {'t': tipo_id})
        print('Tipo de equipamento "Veículo" removido.')
        for nome in MARCAS_ANTIGAS:
            conn.execute(text("""
                DELETE FROM marcas m WHERE m.nome = :n
                AND NOT EXISTS (SELECT 1 FROM marca_tipo_equipamento x WHERE x.marca_id = m.id)
                AND NOT EXISTS (SELECT 1 FROM equipamentos e WHERE e.marca_id = m.id)
                AND NOT EXISTS (SELECT 1 FROM modelos o WHERE o.marca_id = m.id)
            """), {'n': nome})
    conn.execute(text("ALTER TABLE tipos_equipamento DROP COLUMN eh_veiculo"))

    garagem = _um(conn, "SELECT id FROM tipos_sala WHERE nome = 'Garagem / Veículos'")
    if garagem:
        conn.execute(text("""
            DELETE FROM salas s WHERE s.tipo_sala_id = :g AND s.nome = 'Veículos / Garagem'
            AND NOT EXISTS (SELECT 1 FROM equipamentos e WHERE e.sala_id = s.id)
            AND NOT EXISTS (SELECT 1 FROM agenda_eventos a WHERE a.sala_id = s.id)
        """), {'g': garagem})
        if not _um(conn, "SELECT 1 FROM salas WHERE tipo_sala_id = :g", g=garagem):
            conn.execute(text("DELETE FROM kit_padrao_sala WHERE tipo_sala_id = :g"), {'g': garagem})
            conn.execute(text("DELETE FROM tipos_sala WHERE id = :g"), {'g': garagem})
            print('Tipo de sala "Garagem / Veículos" removido.')


app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for sql in COMANDOS:
            conn.execute(text(sql))
        _ligar_agenda_a_veiculos(conn)
        _remover_veiculo_dos_equipamentos(conn)

        novos = 0
        for marca, lista in MODELOS:
            for nome, categoria in lista:
                novos += conn.execute(text("""
                    INSERT INTO veiculo_modelos (marca, nome, categoria) VALUES (:m, :n, :c)
                    ON CONFLICT (marca, nome) DO NOTHING
                """), {'m': marca, 'n': nome, 'c': categoria}).rowcount
        if novos:
            print(f'{novos} modelo(s) de veículo no catálogo.')

        conn.execute(text("""
            INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
            SELECT perfil, 'Veiculos', ver, editar, adicionar FROM perfil_permissoes WHERE secao = 'Equipamentos'
            ON CONFLICT DO NOTHING
        """))

        conn.execute(text("""
            UPDATE tipos_sala SET reservavel = TRUE
            WHERE codigo = 'AMB-41' OR lower(nome) LIKE 'sala de reuni%' OR lower(nome) LIKE 'audit%'
        """))
        grupo = _um(conn, "SELECT grupo FROM tipos_sala WHERE codigo = 'AMB-41'")
        if not _um(conn, "SELECT id FROM tipos_sala WHERE lower(nome) LIKE 'audit%'"):
            conn.execute(text("""
                INSERT INTO tipos_sala (nome, descricao, icone, ativo, grupo, reservavel, criado_em, atualizado_em)
                VALUES ('Auditório', 'Espaço para eventos, capacitações e reuniões grandes. Reservável na agenda.',
                        'fas fa-chalkboard-user', TRUE, :g, TRUE, NOW(), NOW())
            """), {'g': grupo})
            print('Tipo de sala "Auditório" criado.')

        conn.commit()
    print('OK: veículos e reservas de salas/veículos na agenda.')
