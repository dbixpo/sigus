# -*- coding: utf-8 -*-
"""Cria o módulo Segurança do Paciente (NSP) e libera as permissões."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db
from app.models.nsp import CATALOGOS_INICIAIS

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_catalogos (
                id            SERIAL PRIMARY KEY,
                grupo         VARCHAR(40) NOT NULL,
                slug          VARCHAR(50) NOT NULL,
                nome          VARCHAR(150) NOT NULL,
                descricao     TEXT,
                ordem         INTEGER NOT NULL DEFAULT 0,
                ativo         BOOLEAN NOT NULL DEFAULT TRUE,
                cor           VARCHAR(20) NOT NULL DEFAULT 'secondary',
                exige_texto   BOOLEAN NOT NULL DEFAULT FALSE,
                never_event   BOOLEAN NOT NULL DEFAULT FALSE,
                encerra       BOOLEAN NOT NULL DEFAULT FALSE,
                padrao        BOOLEAN NOT NULL DEFAULT FALSE,
                criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_nsp_catalogo_grupo_slug UNIQUE (grupo, slug)
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_catalogos_grupo ON nsp_catalogos (grupo)"
        ))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_ocorrencias (
                id                          SERIAL PRIMARY KEY,
                protocolo                   VARCHAR(20) NOT NULL UNIQUE,
                unidade_id                  INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
                notificante_nome            VARCHAR(150) NOT NULL,
                tipo_setor_notificante_id   INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_notificante_id        INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_notificante_outro     VARCHAR(150),
                nome_afetado                VARCHAR(150),
                data_nascimento             DATE,
                prontuario                  VARCHAR(40),
                tipo_pessoa_id              INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                tipo_pessoa_outro           VARCHAR(150),
                data_ocorrencia             DATE NOT NULL,
                hora_ocorrencia             TIME,
                tipo_setor_ocorrencia_id    INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_ocorrencia_id         INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_ocorrencia_outro      VARCHAR(150),
                departamento_id             INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                tipo_incidente_id           INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                classificacao_id            INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                never_event                 BOOLEAN NOT NULL DEFAULT FALSE,
                descricao                   TEXT NOT NULL,
                acao_imediata               TEXT NOT NULL,
                tipo_setor_notificado_id    INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_notificado_id         INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                setor_notificado_outro      VARCHAR(150),
                status_id                   INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                responsavel_id              INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                fatores_contribuintes       TEXT,
                consequencias_organizacionais TEXT,
                deteccao                    TEXT,
                fatores_atenuantes          TEXT,
                acoes_melhoria              TEXT,
                acoes_reducao_risco         TEXT,
                analise_resumo              TEXT,
                analise_por                 INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                analise_em                  TIMESTAMP,
                notivisa_notificado         BOOLEAN NOT NULL DEFAULT FALSE,
                notivisa_numero             VARCHAR(40),
                notivisa_em                 DATE,
                criado_por                  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em                   TIMESTAMP NOT NULL DEFAULT NOW(),
                atualizado_em               TIMESTAMP NOT NULL DEFAULT NOW(),
                encerrado_em                TIMESTAMP
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_ocorrencias_unidade "
            "ON nsp_ocorrencias (unidade_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_ocorrencias_status "
            "ON nsp_ocorrencias (status_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_ocorrencias_protocolo "
            "ON nsp_ocorrencias (protocolo)"
        ))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_anexos (
                id              SERIAL PRIMARY KEY,
                ocorrencia_id   INTEGER NOT NULL REFERENCES nsp_ocorrencias(id) ON DELETE CASCADE,
                filename        VARCHAR(80) NOT NULL,
                original        VARCHAR(200),
                mime_type       VARCHAR(100),
                tamanho_bytes   INTEGER,
                criado_por      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em       TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_andamentos (
                id              SERIAL PRIMARY KEY,
                ocorrencia_id   INTEGER NOT NULL REFERENCES nsp_ocorrencias(id) ON DELETE CASCADE,
                tipo            VARCHAR(30) NOT NULL DEFAULT 'comentario',
                texto           TEXT NOT NULL,
                criado_por      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em       TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_andamentos_ocorrencia "
            "ON nsp_andamentos (ocorrencia_id)"
        ))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_encaminhamentos (
                id                  SERIAL PRIMARY KEY,
                ocorrencia_id       INTEGER NOT NULL REFERENCES nsp_ocorrencias(id) ON DELETE CASCADE,
                destino_id          INTEGER REFERENCES nsp_catalogos(id) ON DELETE SET NULL,
                destino_outro       VARCHAR(150),
                unidade_destino_id  INTEGER REFERENCES unidades(id) ON DELETE SET NULL,
                texto               TEXT,
                criado_por          INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em           TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_nsp_encaminhamentos_ocorrencia "
            "ON nsp_encaminhamentos (ocorrencia_id)"
        ))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_acoes (
                id                SERIAL PRIMARY KEY,
                ocorrencia_id     INTEGER NOT NULL REFERENCES nsp_ocorrencias(id) ON DELETE CASCADE,
                descricao         TEXT NOT NULL,
                responsavel_nome  VARCHAR(150),
                prazo             DATE,
                concluida         BOOLEAN NOT NULL DEFAULT FALSE,
                concluida_em      TIMESTAMP,
                criado_por        INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em         TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            ALTER TABLE notificacoes
            ADD COLUMN IF NOT EXISTS nsp_ocorrencia_id INTEGER
            REFERENCES nsp_ocorrencias(id) ON DELETE CASCADE
        """))

        for row in CATALOGOS_INICIAIS:
            grupo, slug, nome, ordem, cor, exige_texto, never_event, encerra, padrao = row
            conn.execute(text("""
                INSERT INTO nsp_catalogos
                    (grupo, slug, nome, ordem, cor, exige_texto, never_event, encerra, padrao)
                VALUES
                    (:grupo, :slug, :nome, :ordem, :cor, :exige_texto, :never_event, :encerra, :padrao)
                ON CONFLICT (grupo, slug) DO NOTHING
            """), {
                'grupo': grupo, 'slug': slug, 'nome': nome, 'ordem': ordem, 'cor': cor,
                'exige_texto': exige_texto, 'never_event': never_event,
                'encerra': encerra, 'padrao': padrao,
            })

        conn.execute(text("""
            INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
            SELECT perfil, 'SegurancaPaciente', ver, editar, adicionar
            FROM perfil_permissoes
            WHERE secao = 'Planejamentos'
            ON CONFLICT (perfil, secao) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO perfil_permissoes (perfil, secao, ver, editar, adicionar)
            VALUES
                ('profissional', 'SegurancaPaciente', TRUE, FALSE, TRUE),
                ('administrativo', 'SegurancaPaciente', TRUE, TRUE, TRUE),
                ('coordenador', 'SegurancaPaciente', TRUE, TRUE, TRUE),
                ('gestor_secretaria', 'SegurancaPaciente', TRUE, TRUE, TRUE),
                ('administrador', 'SegurancaPaciente', TRUE, TRUE, TRUE)
            ON CONFLICT (perfil, secao) DO UPDATE SET
                ver = EXCLUDED.ver OR perfil_permissoes.ver,
                editar = EXCLUDED.editar OR perfil_permissoes.editar,
                adicionar = EXCLUDED.adicionar OR perfil_permissoes.adicionar
        """))
        conn.commit()
    print('OK: tabelas NSP, catálogos iniciais e permissão SegurancaPaciente.')
