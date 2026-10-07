# -*- coding: utf-8 -*-
"""Segurança do Paciente no fluxo do SNI-SGQSP: Núcleo, comissões, qualificação e investigação."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

COLUNAS_OCORRENCIA = [
    ("etapa", "VARCHAR(20) NOT NULL DEFAULT 'em_qualificacao'"),
    ("origem", "VARCHAR(10) NOT NULL DEFAULT 'sigus'"),
    ("anonimo", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("tipologia", "VARCHAR(60)"),
    ("local_incidente", "VARCHAR(150)"),
    ("turno", "VARCHAR(30)"),
    ("ocorrencia_em", "TIMESTAMP"),
    ("identificacao_em", "TIMESTAMP"),
    ("paciente_codigo", "VARCHAR(60)"),
    ("faixa_etaria", "VARCHAR(10)"),
    ("notificante_cargo", "VARCHAR(120)"),
    ("qual_classificacao", "VARCHAR(60)"),
    ("qual_dano", "VARCHAR(20)"),
    ("qual_criticidade", "VARCHAR(20)"),
    ("qual_diagnostico", "TEXT"),
    ("qual_fundamentacao", "TEXT"),
    ("qualificado_por", "INTEGER REFERENCES usuarios(id) ON DELETE SET NULL"),
    ("qualificado_em", "TIMESTAMP"),
    ("inv_metodologia", "VARCHAR(40)"),
    ("inv_status", "VARCHAR(20)"),
    ("inv_barreiras", "TEXT"),
    ("inv_causas", "TEXT"),
    ("inv_conclusao", "TEXT"),
    ("inv_por", "INTEGER REFERENCES usuarios(id) ON DELETE SET NULL"),
    ("inv_em", "TIMESTAMP"),
]

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for nome, tipo in COLUNAS_OCORRENCIA:
            conn.execute(text(f"ALTER TABLE nsp_ocorrencias ADD COLUMN IF NOT EXISTS {nome} {tipo}"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nsp_ocorrencias_etapa ON nsp_ocorrencias (etapa)"))
        conn.execute(text("ALTER TABLE nsp_ocorrencias ALTER COLUMN notificante_nome DROP NOT NULL"))
        conn.execute(text("ALTER TABLE nsp_ocorrencias ALTER COLUMN acao_imediata DROP NOT NULL"))

        conn.execute(text(
            "ALTER TABLE nsp_encaminhamentos ADD COLUMN IF NOT EXISTS liberado_coordenacao BOOLEAN NOT NULL DEFAULT FALSE"))
        conn.execute(text(
            "ALTER TABLE nsp_encaminhamentos ADD COLUMN IF NOT EXISTS liberado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL"))
        conn.execute(text("ALTER TABLE nsp_encaminhamentos ADD COLUMN IF NOT EXISTS liberado_em TIMESTAMP"))

        conn.execute(text("ALTER TABLE nsp_acoes ADD COLUMN IF NOT EXISTS indicador VARCHAR(255)"))
        conn.execute(text("ALTER TABLE nsp_acoes ADD COLUMN IF NOT EXISTS status VARCHAR(20)"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nsp_membros (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                papel VARCHAR(20) NOT NULL,
                unidade_id INTEGER REFERENCES unidades(id) ON DELETE CASCADE,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_nsp_membro UNIQUE (usuario_id, papel, unidade_id)
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nsp_membros_usuario_id ON nsp_membros (usuario_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_nsp_membros_unidade_id ON nsp_membros (unidade_id)"))

        # Registros do fluxo antigo: etapa a partir do status e notificante não identificado.
        conn.execute(text("""
            UPDATE nsp_ocorrencias o SET etapa = CASE
                WHEN c.slug IN ('concluido') THEN 'concluida'
                WHEN c.slug IN ('arquivado') THEN 'arquivada'
                WHEN c.slug IN ('encaminhado', 'plano_acao') THEN 'encaminhada'
                WHEN c.slug = 'em_analise' THEN 'em_investigacao'
                ELSE 'em_qualificacao' END,
                anonimo = FALSE
            FROM nsp_catalogos c
            WHERE c.id = o.status_id AND o.ocorrencia_em IS NULL AND o.origem = 'sigus'
              AND o.tipologia IS NULL
        """))
        conn.execute(text("""
            UPDATE nsp_acoes SET status = CASE WHEN concluida THEN 'Concluída' ELSE 'Aberta' END
            WHERE status IS NULL
        """))
        conn.commit()
    print('OK: fluxo SNI-SGQSP (Núcleo, comissões, qualificação, investigação).')
