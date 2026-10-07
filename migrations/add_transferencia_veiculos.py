# -*- coding: utf-8 -*-
"""Veículos nos termos de empréstimo/transferência (idempotente).

- itens_documento_transferencia.veiculo_id (→ veiculos)
- documentos_transferencia: devolucao_prevista, devolvido_em, devolvido_por
  (empréstimo de veículo fica ativo do aceite até alguém clicar em "Devolver")
- agenda_eventos.condutor_unidade_id: reserva de veículo para pessoa de outra unidade
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app import create_app, db

COMANDOS = [
    "ALTER TABLE itens_documento_transferencia ADD COLUMN IF NOT EXISTS veiculo_id INTEGER "
    "REFERENCES veiculos(id) ON DELETE SET NULL",
    "ALTER TABLE documentos_transferencia ADD COLUMN IF NOT EXISTS devolucao_prevista DATE",
    "ALTER TABLE documentos_transferencia ADD COLUMN IF NOT EXISTS devolvido_em TIMESTAMP",
    "ALTER TABLE documentos_transferencia ADD COLUMN IF NOT EXISTS devolvido_por INTEGER "
    "REFERENCES usuarios(id) ON DELETE SET NULL",
    "ALTER TABLE agenda_eventos ADD COLUMN IF NOT EXISTS condutor_unidade_id INTEGER "
    "REFERENCES unidades(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_itens_doc_transf_veiculo ON itens_documento_transferencia (veiculo_id) "
    "WHERE veiculo_id IS NOT NULL",
]

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        for sql in COMANDOS:
            conn.execute(text(sql))
        conn.commit()
    print('OK: veículos nos termos de empréstimo/transferência.')
