# -*- coding: utf-8 -*-
"""Veículos das unidades e reserva de salas/veículos na agenda (idempotente).

- tipos_equipamento.eh_veiculo, tipos_sala.reservavel, salas.uso_compartilhado
- agenda_eventos: sala_id, veiculo_id, condutor_id, km_saida, km_chegada, devolvido_em
- Tipo de equipamento "Veículo" (sem patrimônio: prefixo + check "Alugado") com os campos
  do carro e marcas mais comuns
- Tipos de sala: "Sala de Reunião" (AMB-41) passa a ser reservável; cria "Auditório"
  (reservável) e "Garagem / Veículos" (onde ficam os carros da unidade)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

COMANDOS = [
    "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS eh_veiculo BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE tipos_sala ADD COLUMN IF NOT EXISTS reservavel BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE salas ADD COLUMN IF NOT EXISTS uso_compartilhado BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS sala_id INTEGER REFERENCES salas(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS veiculo_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS condutor_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS km_saida INTEGER",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS km_chegada INTEGER",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS devolvido_em TIMESTAMP",
    "CREATE INDEX IF NOT EXISTS ix_agenda_eventos_sala ON agenda_eventos (sala_id, inicio) WHERE sala_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_agenda_eventos_veiculo ON agenda_eventos (veiculo_id, inicio) WHERE veiculo_id IS NOT NULL",
]

CAMPOS_VEICULO = [
    # (nome, tipo_dado, obrigatório, opções, destaque)
    # Veículo não tem patrimônio: é identificado pelo prefixo (383; alugado aparece como AL-383).
    ('Prefixo', 'texto', True, None, False),
    ('Alugado', 'booleano', False, None, False),
    ('Placa', 'texto', True, None, True),
    ('Categoria', 'selecao', True, ['Carro de passeio', 'Utilitário', 'Caminhonete', 'Van',
                                    'Micro-ônibus / ônibus', 'Ambulância', 'Motocicleta', 'Caminhão'], False),
    ('Ano fabricação/modelo', 'texto', False, None, False),
    ('Cor', 'texto', False, None, False),
    ('Combustível', 'selecao', False, ['Flex', 'Gasolina', 'Etanol', 'Diesel', 'GNV', 'Elétrico', 'Híbrido'], False),
    ('Lotação (passageiros)', 'numero', False, None, False),
    ('RENAVAM', 'texto', False, None, False),
    ('Chassi', 'texto', False, None, False),
    ('Locadora / contrato', 'texto', False, None, False),
    ('Km no cadastro', 'numero', False, None, False),
    ('Licenciamento (vencimento)', 'texto', False, None, False),
]

MARCAS_VEICULO = [
    'Fiat', 'Volkswagen', 'Chevrolet', 'Renault', 'Ford', 'Toyota', 'Hyundai', 'Peugeot',
    'Citroën', 'Nissan', 'Honda', 'Jeep', 'Mercedes-Benz', 'Iveco', 'Mitsubishi',
]


def _id(conn, sql, **params):
    row = conn.execute(text(sql), params).first()
    return row[0] if row else None


app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for sql in COMANDOS:
            conn.execute(text(sql))

        tipo_id = _id(conn, "SELECT id FROM tipos_equipamento WHERE eh_veiculo ORDER BY id LIMIT 1") \
            or _id(conn, "SELECT id FROM tipos_equipamento WHERE lower(nome) = 'veículo'")
        if not tipo_id:
            tipo_id = _id(conn, """
                INSERT INTO tipos_equipamento (nome, descricao, tem_patrimonio, icone, ativo, classificacao,
                                               eh_veiculo, criado_em, atualizado_em)
                VALUES ('Veículo', 'Carros, vans e demais veículos da unidade. Têm aba própria na unidade, '
                        'reserva na agenda e RDV mensal.', TRUE, 'fas fa-car', TRUE, 'Veículos', TRUE, NOW(), NOW())
                RETURNING id
            """)
            print('Tipo "Veículo" criado.')
        conn.execute(text("UPDATE tipos_equipamento SET eh_veiculo = TRUE, tem_patrimonio = FALSE WHERE id = :id"),
                     {'id': tipo_id})

        for ordem, (nome, tipo_dado, obrig, opcoes, destaque) in enumerate(CAMPOS_VEICULO, start=1):
            existe = _id(conn, "SELECT id FROM campos_tipo_equipamento WHERE tipo_equipamento_id = :t AND nome_campo = :n",
                         t=tipo_id, n=nome)
            if existe:
                conn.execute(text("UPDATE campos_tipo_equipamento SET ordem = :o WHERE id = :id"),
                             {'o': ordem, 'id': existe})
                continue
            conn.execute(text("""
                INSERT INTO campos_tipo_equipamento (tipo_equipamento_id, nome_campo, tipo_dado, obrigatorio,
                                                     opcoes_selecao, ordem, campo_destaque, criado_em)
                VALUES (:t, :n, :d, :o, CAST(:op AS JSON), :ordem, :dest, NOW())
            """), {'t': tipo_id, 'n': nome, 'd': tipo_dado, 'o': obrig,
                   'op': None if opcoes is None else json.dumps(opcoes, ensure_ascii=False),
                   'ordem': ordem, 'dest': destaque})
            print(f'Campo "{nome}" criado.')

        # "Vínculo" (próprio/locado/cedido) virou o check "Alugado".
        vinculo = _id(conn, "SELECT id FROM campos_tipo_equipamento WHERE tipo_equipamento_id = :t AND nome_campo = 'Vínculo'",
                      t=tipo_id)
        if vinculo:
            alugado = _id(conn, "SELECT id FROM campos_tipo_equipamento WHERE tipo_equipamento_id = :t AND nome_campo = 'Alugado'",
                          t=tipo_id)
            conn.execute(text("""
                INSERT INTO equipamento_campo_valores (equipamento_id, campo_id, valor)
                SELECT equipamento_id, :alugado, 'sim' FROM equipamento_campo_valores
                WHERE campo_id = :vinculo AND valor = 'Locado'
                ON CONFLICT (equipamento_id, campo_id) DO NOTHING
            """), {'alugado': alugado, 'vinculo': vinculo})
            conn.execute(text("DELETE FROM campos_tipo_equipamento WHERE id = :id"), {'id': vinculo})
            print('Campo "Vínculo" trocado pelo check "Alugado".')

        for nome in MARCAS_VEICULO:
            marca_id = _id(conn, "SELECT id FROM marcas WHERE lower(nome) = lower(:n)", n=nome)
            if not marca_id:
                marca_id = _id(conn, "INSERT INTO marcas (nome, criado_em, atualizado_em) VALUES (:n, NOW(), NOW()) RETURNING id",
                               n=nome)
            conn.execute(text("""
                INSERT INTO marca_tipo_equipamento (marca_id, tipo_equipamento_id) VALUES (:m, :t)
                ON CONFLICT DO NOTHING
            """), {'m': marca_id, 't': tipo_id})

        conn.execute(text("""
            UPDATE tipos_sala SET reservavel = TRUE
            WHERE codigo = 'AMB-41' OR lower(nome) LIKE 'sala de reuni%' OR lower(nome) LIKE 'audit%'
        """))
        grupo = _id(conn, "SELECT grupo FROM tipos_sala WHERE codigo = 'AMB-41'")
        if not _id(conn, "SELECT id FROM tipos_sala WHERE lower(nome) LIKE 'audit%'"):
            conn.execute(text("""
                INSERT INTO tipos_sala (nome, descricao, icone, ativo, grupo, reservavel, criado_em, atualizado_em)
                VALUES ('Auditório', 'Espaço para eventos, capacitações e reuniões grandes. Reservável na agenda.',
                        'fas fa-chalkboard-user', TRUE, :g, TRUE, NOW(), NOW())
            """), {'g': grupo})
            print('Tipo de sala "Auditório" criado.')
        if not _id(conn, "SELECT id FROM tipos_sala WHERE lower(nome) LIKE 'garagem%'"):
            conn.execute(text("""
                INSERT INTO tipos_sala (nome, descricao, icone, ativo, reservavel, criado_em, atualizado_em)
                VALUES ('Garagem / Veículos', 'Onde ficam os veículos da unidade. Criada automaticamente '
                        'ao cadastrar o primeiro veículo.', 'fas fa-warehouse', TRUE, FALSE, NOW(), NOW())
            """))
            print('Tipo de sala "Garagem / Veículos" criado.')

        conn.commit()
    print('OK: veículos e reservas de salas/veículos na agenda.')
