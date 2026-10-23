# -*- coding: utf-8 -*-
"""Tira da auditoria o ruído do sino e do manifesto e junta o mapa num módulo só.

Não apaga login, alteração, mural, frequência nem o restante.
Pode rodar de novo.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db

app = create_app()
with app.app_context():
    db.session.execute(db.text(
        "CREATE INDEX IF NOT EXISTS ix_auditoria_created ON auditoria (created_at DESC)"
    ))
    db.session.execute(db.text(
        "CREATE INDEX IF NOT EXISTS ix_auditoria_modulo ON auditoria (modulo)"
    ))
    apagados = db.session.execute(db.text("""
        DELETE FROM auditoria
        WHERE endpoint IN ('notificacoes.recentes', 'notificacoes.contagem', 'manifest')
           OR modulo = 'manifest'
    """)).rowcount
    mapa = db.session.execute(db.text("""
        UPDATE auditoria
           SET modulo = 'mapa_da_saude'
         WHERE modulo LIKE 'mapa_da_saude%'
           AND modulo <> 'mapa_da_saude'
    """)).rowcount
    db.session.commit()
    with open(os.path.join('scripts', '_tmp_aud_limpeza.txt'), 'w', encoding='utf-8') as f:
        f.write(f'apagados={apagados} mapa_unificado={mapa}\n')
os._exit(0)
