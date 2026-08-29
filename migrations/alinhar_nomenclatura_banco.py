# -*- coding: utf-8 -*-
"""
Migração: Alinha nomenclatura do banco com o código.

Renomeia tabelas e colunas para remover a camada de conversão:
- planos → planejamentos
- planos_anexos → planejamentos_anexos, plano_id → planejamento_id
- acoes_plano → acoes_planejamento, plano_id → planejamento_id
- acoes_plano_observacoes → acoes_planejamento_observacoes
- acoes_plano_obs_anexos → acoes_planejamento_obs_anexos
- acacao_responsaveis → acao_planejamento_responsaveis
- acacao_empresas → acao_planejamento_empresas
- auditoria.user_id → usuario_id

Execute UMA VEZ após ter o banco atualizado.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        # 1. planos → planejamentos
        conn.execute(text('ALTER TABLE planos RENAME TO planejamentos'))

        # 2. planos_anexos → planejamentos_anexos
        conn.execute(text('ALTER TABLE planos_anexos RENAME TO planejamentos_anexos'))
        conn.execute(text('ALTER TABLE planejamentos_anexos RENAME COLUMN plano_id TO planejamento_id'))

        # 3. acoes_plano → acoes_planejamento
        conn.execute(text('ALTER TABLE acoes_plano RENAME TO acoes_planejamento'))
        conn.execute(text('ALTER TABLE acoes_planejamento RENAME COLUMN plano_id TO planejamento_id'))

        # 4. acoes_plano_observacoes → acoes_planejamento_observacoes
        conn.execute(text('ALTER TABLE acoes_plano_observacoes RENAME TO acoes_planejamento_observacoes'))

        # 5. acoes_plano_obs_anexos → acoes_planejamento_obs_anexos
        conn.execute(text('ALTER TABLE acoes_plano_obs_anexos RENAME TO acoes_planejamento_obs_anexos'))

        # 6. acacao_responsaveis → acao_planejamento_responsaveis
        conn.execute(text('ALTER TABLE acacao_responsaveis RENAME TO acao_planejamento_responsaveis'))

        # 7. acacao_empresas → acao_planejamento_empresas
        conn.execute(text('ALTER TABLE acacao_empresas RENAME TO acao_planejamento_empresas'))

        # 8. auditoria.user_id → usuario_id
        conn.execute(text('ALTER TABLE auditoria RENAME COLUMN user_id TO usuario_id'))

        trans.commit()
        print('OK: Nomenclatura do banco alinhada com o código.')
    except Exception as e:
        trans.rollback()
        print(f'ERRO: {e}')
        raise
