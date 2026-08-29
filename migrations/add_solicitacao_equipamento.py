"""Adiciona tipo de chamado Solicitação de Equipamento (SE) e tabela de itens."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE chamados ADD COLUMN IF NOT EXISTS se_tipo_equipamento_id INTEGER "
            "REFERENCES tipos_equipamento(id) ON DELETE SET NULL"
        ))
        conn.commit()

    from app.models.chamado import ChamadoSolicitacaoItem
    ChamadoSolicitacaoItem.__table__.create(db.engine, checkfirst=True)

    print("OK: migração add_solicitacao_equipamento concluída.")
