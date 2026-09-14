# -*- coding: utf-8 -*-
"""Índices para acelerar a listagem de planejamentos e alertas de prazo."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

INDEXES = [
    ('ix_acoes_planejamento_plano', 'acoes_planejamento', '(planejamento_id)'),
    ('ix_acoes_planejamento_prazo_status', 'acoes_planejamento', '(prazo, status)'),
    ('ix_planejamentos_unidade', 'planejamentos', '(unidade_id)'),
    ('ix_obs_acao', 'acoes_planejamento_observacoes', '(acao_id)'),
    ('ix_notificacoes_usuario_lida', 'notificacoes', '(usuario_id, lida)'),
    ('ix_notificacoes_usuario_tipo', 'notificacoes', '(usuario_id, tipo)'),
    ('ix_pu_unidade', 'planejamento_unidades', '(unidade_id)'),
    ('ix_ptu_tipo', 'planejamento_tipos_unidade', '(tipo_unidade_id)'),
    ('ix_planos_anexos_plano', 'planejamentos_anexos', '(planejamento_id)'),
    ('ix_uu_unidade_ativo', 'usuario_unidade', '(unidade_id, ativo)'),
]

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for nome, tabela, cols in INDEXES:
            conn.execute(text(
                f'CREATE INDEX IF NOT EXISTS {nome} ON {tabela} {cols}'
            ))
        conn.commit()
    print('OK: índices de planejamentos/notificações.')
